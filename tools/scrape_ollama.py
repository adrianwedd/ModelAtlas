import asyncio
import json
import hashlib
import re
import time
import os
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from atlas_schemas.config import settings
from common.logging import logger, LOG_FORMAT
from logging.handlers import RotatingFileHandler
import logging

LOG_FILE = settings.LOG_FILE
OLLAMA_MODELS_DIR = settings.MODELS_DIR / "ollama"
DEBUG_DIR = settings.DEBUG_DIR

LAYER_MEDIA_TYPE_MAP = {
    "application/vnd.ollama.image.model": "Model Weights",
    "application/vnd.ollama.image.license": "License",
    "application/vnd.ollama.image.template": "Template",
    "application/vnd.ollama.image.params": "Parameters",
}

LICENSE_MAP = {
    "mit": "MIT",
    "apache-2.0": "Apache-2.0",
}


def parse_pull_count(s: str | None) -> int:
    if not s:
        return 0
    s = s.replace("Pulls", "").replace("Downloads", "").strip()
    try:
        if "M" in s:
            return int(float(s.replace("M", "")) * 1e6)
        if "K" in s:
            return int(float(s.replace("K", "")) * 1e3)
        return int(float(s))
    except Exception:
        return 0

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]

def normalize_layer_media_type(media_type: str) -> str | None:
    if not media_type:
        return None
    return LAYER_MEDIA_TYPE_MAP.get(media_type, media_type)

def normalize_license(license_str: str) -> str | None:
    if not license_str:
        return None
    license_str = license_str.lower().strip()
    return LICENSE_MAP.get(license_str, license_str)

async def fetch(client: httpx.AsyncClient, url: str) -> str:
    logger.info("Fetching: %s", url)
    resp = await client.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text

async def fetch_json(client: httpx.AsyncClient, url: str) -> dict | None:
    logger.info("Fetching JSON: %s", url)
    try:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        logger.error("Error fetching %s: %s", url, e)
        return None

async def fetch_manifest(client: httpx.AsyncClient, model: str, tag: str = "latest") -> dict | None:
    url = f"https://registry.ollama.ai/v2/library/{model}/manifests/{tag}"
    return await fetch_json(client, url)

async def decode_manifest_config(client: httpx.AsyncClient, model_name: str, digest: str) -> dict | None:
    url = f"https://registry.ollama.ai/v2/library/{model_name}/blobs/{digest}"
    return await fetch_json(client, url)

async def scrape_tags_page(client: httpx.AsyncClient, model_name: str) -> list[dict]:
    url = f"https://ollama.com/library/{model_name}/tags"
    html = await fetch(client, url)
    soup = BeautifulSoup(html, "html.parser")
    tags_data = []
    for item in soup.select("div.group.px-4.py-3"):
        tag_elem = item.find("a")
        if not tag_elem:
            continue
        tag_name = tag_elem.text.strip()
        size_elem = item.find("p", class_="col-span-2")
        size = size_elem.get_text(strip=True) if size_elem else ""
        details_div = item.find("div", class_="flex text-neutral-500 text-xs items-center")
        digest = ""
        last_updated = ""
        if details_div:
            digest_elem = details_div.find("span", class_="font-mono")
            digest = digest_elem.get_text(strip=True) if digest_elem else ""
            last_updated_match = re.search(r"·\s*(.*)", details_div.get_text(strip=True))
            if last_updated_match:
                last_updated = last_updated_match.group(1).strip()
        api_tag = tag_name.split(":")[-1]
        tag_entry = {
            "tag": tag_name,
            "last_updated": last_updated,
            "size": size.replace("·", "").strip(),
            "digest": digest,
            "manifest": None,
            "config": {},
        }
        manifest = await fetch_manifest(client, model_name, api_tag)
        if manifest:
            tag_entry["manifest"] = manifest
            if manifest.get("config") and manifest["config"].get("digest"):
                tag_entry["digest"] = manifest["config"]["digest"]
                cfg = await decode_manifest_config(client, model_name, tag_entry["digest"])
                if cfg:
                    tag_entry["config"] = cfg
                    tag_entry["context_length"] = cfg.get("parameters", {}).get("context_window")
                    tag_entry["model_type"] = cfg.get("model_type")
                    tag_entry["quantization"] = cfg.get("quantization")
                    tag_entry["base_model"] = cfg.get("base_model")
            for layer in manifest.get("layers", []):
                layer["mediaType"] = normalize_layer_media_type(layer.get("mediaType"))
                if layer.get("annotations"):
                    if "ollama.context_window" in layer["annotations"] and not tag_entry.get("context_length"):
                        tag_entry["context_length"] = layer["annotations"]["ollama.context_window"]
                    if "ollama.input_type" in layer["annotations"] and not tag_entry.get("model_type"):
                        tag_entry["model_type"] = layer["annotations"]["ollama.input_type"]
        tags_data.append(tag_entry)
    logger.info("Found %s tag items on the page.", len(tags_data))
    return tags_data

async def scrape_details(client: httpx.AsyncClient, model_name: str) -> dict:
    url = f"https://ollama.com/library/{model_name}"
    html = await fetch(client, url)
    soup = BeautifulSoup(html, "html.parser")
    result: dict = {"name": model_name}
    m = soup.find("meta", {"name": "description"})
    result["description"] = m["content"].strip() if m else ""
    lic_match = re.search(r"licensed under the ([\w\-]+)", html, re.IGNORECASE)
    if lic_match:
        result["license"] = normalize_license(lic_match.group(1))
    pull_span = soup.find("span", attrs={"x-test-pull-count": True})
    if pull_span:
        result["pull_count"] = parse_pull_count(pull_span.text.strip())
    last_span = soup.find("span", attrs={"x-test-updated": True})
    if last_span and last_span.parent and last_span.parent.has_attr("title"):
        result["last_updated"] = last_span.parent["title"]
    else:
        result["last_updated"] = last_span.text.strip() if last_span else ""
    prose = soup.find("div", class_="prose")
    result["readme_html"] = str(prose) if prose else ""
    content_txt = prose.get_text(" ") if prose else ""
    result["readme_text"] = prose.get_text() if prose else ""
    m_arch = re.search(r"architecture:\s*([\w\-]+)", content_txt, re.IGNORECASE)
    if m_arch:
        result["architecture"] = m_arch.group(1)
    m_family = re.search(r"family:\s*([\w\-]+)", content_txt, re.IGNORECASE)
    if m_family:
        result["family"] = m_family.group(1)
    result["page_hash"] = get_hash(soup.prettify())
    return result

async def fetch_model_list(client: httpx.AsyncClient) -> list[str]:
    url = "https://ollama.com/library"
    html = await fetch(client, url)
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("ul[role=list] > li")
    names = [
        i.find("a")["href"].split("/")[-1]
        for i in items
        if i.find("a") and "/library/" in i.find("a")["href"]
    ]
    logger.info("Found %s models on Ollama.com", len(names))
    return names

async def process_model(client: httpx.AsyncClient, name: str, semaphore: asyncio.Semaphore) -> dict | None:
    async with semaphore:
        logger.info("==> Processing Ollama.com model: %s", name)
        model_file_path = OLLAMA_MODELS_DIR / f"{name.replace('/', '_')}.json"
        existing = {}
        if model_file_path.exists():
            existing = json.loads(model_file_path.read_text(encoding="utf-8"))
        detail = await scrape_details(client, name)
        if existing.get("page_hash") == detail.get("page_hash"):
            logger.info("Page hash for %s matches existing data. Skipping detailed scrape.", name)
            data = existing
        else:
            logger.info("Page hash for %s changed or no existing data. Performing full scrape.", name)
            tags = await scrape_tags_page(client, name)
            detail["tags"] = tags
            data = detail
        model_file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

async def scrape_ollama_models(concurrency: int = 5, debug_model: str | None = None) -> list[dict]:
    os.makedirs(OLLAMA_MODELS_DIR, exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)
    for handler in list(logger.handlers):
        if isinstance(handler, RotatingFileHandler):
            logger.removeHandler(handler)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    results = []
    async with httpx.AsyncClient() as client:
        names = await fetch_model_list(client)
        if debug_model:
            names = [n for n in names if n == debug_model]
            if not names:
                logger.error("Debug model '%s' not found in Ollama.com initial list.", debug_model)
                return []
        semaphore = asyncio.Semaphore(concurrency)
        tasks = [process_model(client, n, semaphore) for n in names]
        results = [r for r in await asyncio.gather(*tasks) if r]
    logger.info("Ollama.com scraping complete — %s models stored in %s", len(results), OLLAMA_MODELS_DIR)
    return results

if __name__ == "__main__":
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--debug-model")
    args = parser.parse_args()
    asyncio.run(scrape_ollama_models(concurrency=args.concurrency, debug_model=args.debug_model))
