"""
Stage 2: Reverse Image Search
Uses SerpApi Google Lens to search for the image on the web.
Filters results to social media domains and saves the best match to output/matched_post.json.
"""

import os
import json
import sys
import requests
from typing import Optional
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv

# Social media domains to search for
SOCIAL_MEDIA_DOMAINS = {
    'twitter.com',
    'x.com',
    'instagram.com',
    'linkedin.com',
    'facebook.com',
    'reddit.com',
    'tiktok.com',
    'youtube.com'
}


def is_social_media_url(url: str) -> bool:
    """Check if URL belongs to a social media domain"""
    try:
        domain = urlparse(url).netloc.lower()
        # Remove www. prefix if present
        domain = domain.replace('www.', '')
        return any(social_domain in domain for social_domain in SOCIAL_MEDIA_DOMAINS)
    except Exception:
        return False


def _raise_serpapi_error(response: requests.Response, operation: str) -> None:
    """Raise an actionable error for common SerpApi response failures."""
    if response.status_code == 401:
        raise ValueError(
            "SerpApi authentication failed (HTTP 401). Check that SERPAPI_API_KEY "
            "is valid and active."
        )
    if response.status_code == 404:
        raise RuntimeError(
            f"SerpApi {operation} endpoint was not found (HTTP 404). "
            "Use the documented /image upload and /search endpoints."
        )
    if response.status_code == 429:
        raise RuntimeError(
            "SerpApi rate limit reached (HTTP 429). Check your plan usage and retry later."
        )
    try:
        details = response.json().get("error", response.text[:200])
    except ValueError:
        details = response.text[:200]
    raise RuntimeError(
        f"SerpApi {operation} failed (HTTP {response.status_code}): {details}"
    )


def _raise_api_payload_error(data: dict, operation: str) -> None:
    """Classify errors returned inside an otherwise successful JSON response."""
    error = str(data.get("error", ""))
    if not error:
        return
    lowered_error = error.lower()
    if "auth" in lowered_error or "api key" in lowered_error or "invalid key" in lowered_error:
        raise ValueError(f"SerpApi authentication failed during {operation}: {error}")
    if "rate" in lowered_error or "limit" in lowered_error:
        raise RuntimeError(f"SerpApi rate limit reached during {operation}: {error}")
    raise RuntimeError(f"SerpApi {operation} failed: {error}")


def reverse_image_search(image_path: str, output_dir: str = "output") -> Optional[dict]:
    """
    Performs a reverse image search using SerpApi's Google Lens engine.
    
    Args:
        image_path: Path to the input image file
        output_dir: Directory to save the matched post JSON
        
    Returns:
        dict: Contains title, URL, and thumbnail of the matched post
        
    Raises:
        FileNotFoundError: If image file doesn't exist
        Exception: If API call fails or no social media matches found
    """
    
    load_dotenv()

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "matched_post.json")
    if os.path.isfile(output_file):
        os.remove(output_file)
    
    # Validate input file
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Get API key from environment
    api_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError(
            "SERPAPI_API_KEY environment variable not set. "
            "Get a key from https://serpapi.com/ and set it in .env"
        )
    api_key = api_key.strip()
    if not api_key:
        raise ValueError("SERPAPI_API_KEY is empty. Add a valid SerpApi key to .env")
    
    print(f"[Stage 2] Performing reverse image search: {image_path}")
    
    try:
        # Read the image file and upload it to obtain SerpApi's temporary image_id.
        with open(image_path, "rb") as f:
            image_data = f.read()

        if len(image_data) > 500 * 1024:
            raise ValueError("Image is larger than SerpApi's 500 KB upload limit")

        print(f"  → Uploading image to SerpApi (key length: {len(api_key)})...")
        upload_response = requests.post(
            "https://serpapi.com/image",
            data={"api_key": api_key},
            files={"image": (os.path.basename(image_path), image_data)},
            timeout=30,
        )
        if not upload_response.ok:
            _raise_serpapi_error(upload_response, "image upload")
        upload_data = upload_response.json()
        _raise_api_payload_error(upload_data, "image upload")
        image_id = upload_data.get("image_id")
        if not image_id:
            raise RuntimeError("SerpApi image upload returned no image_id")

        print("  → Searching Google Lens with uploaded image...")
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google_lens",
                "image_id": image_id,
                "type": "visual_matches",
                "api_key": api_key,
            },
            timeout=30,
        )
        if not response.ok:
            _raise_serpapi_error(response, "Google Lens search")
        data = response.json()
        _raise_api_payload_error(data, "Google Lens search")
        
        # Extract results
        results = data.get("visual_matches", [])
        
        if not results:
            print("  ⚠ No results from SerpApi. Image may not exist online yet.")
            return None
        
        # Filter for social media results
        social_media_results = [
            r for r in results
            if is_social_media_url(r.get("link", ""))
        ]
        
        if not social_media_results:
            print("  ⚠ No social media matches found. Trying best overall match...")
            matched_result = results[0]  # Fall back to best overall match
        else:
            matched_result = social_media_results[0]
            print(f"  → Found {len(social_media_results)} social media match(es)")
        
        # Extract and structure the matched post data
        matched_post = {
            "title": matched_result.get("title", ""),
            "url": matched_result.get("link", ""),
            "thumbnail": matched_result.get("thumbnail", ""),
            "source": urlparse(matched_result.get("link", "")).netloc,
            "timestamp": datetime.now().isoformat(),
            "image_searched": image_path
        }
        
        # Validate that we have meaningful data
        if not matched_post["url"]:
            raise ValueError("Matched result has no URL")
        
        # Save matched post to output file
        with open(output_file, "w") as f:
            json.dump(matched_post, f, indent=2)
        
        print(f"  ✓ Matched post found:")
        print(f"    Title: {matched_post['title'][:60]}...")
        print(f"    URL: {matched_post['url']}")
        print(f"    Source: {matched_post['source']}")
        print(f"  ✓ Match saved to: {output_file}")
        
        return matched_post
    
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network request failed: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse API response: {e}")
        raise
    except Exception as e:
        print(f"ERROR: Reverse image search failed: {e}")
        raise


def main(image_path: str):
    """Main entry point for stage 2"""
    try:
        result = reverse_image_search(image_path)
        if result:
            print("\n[Stage 2] ✓ SUCCESS: Web search completed\n")
        else:
            print("\n[Stage 2] ⚠ WARNING: No results found, continuing anyway\n")
        return result
    except FileNotFoundError as e:
        print(f"\n[Stage 2] ✗ FAILED: {e}\n")
        return None
    except ValueError as e:
        print(f"\n[Stage 2] ✗ FAILED: {e}\n")
        return None
    except Exception as e:
        print(f"\n[Stage 2] ✗ FAILED: {e}\n")
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "input_face.jpg"
    
    main(image_path)
