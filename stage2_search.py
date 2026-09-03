"""
Stage 2: Reverse Image Search
Uses SerpApi Google Lens to search for the image on the web.
Filters results to social media domains and saves the best match to output/matched_post.json.
"""

import os
import json
import sys
import requests
from urllib.parse import urlparse
from datetime import datetime

try:
    import serpapi
except ImportError:
    print("ERROR: google-search-results not installed. Run: pip install google-search-results")
    sys.exit(1)


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


def reverse_image_search(image_path: str, output_dir: str = "output") -> dict:
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
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Validate input file
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Get API key from environment
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError(
            "SERPAPI_KEY environment variable not set. "
            "Get a key from https://serpapi.com/ and set it in .env"
        )
    
    print(f"[Stage 2] Performing reverse image search: {image_path}")
    
    try:
        # Read the image file and prepare for upload
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Use SerpApi's google_lens engine for reverse image search
        # Documentation: https://serpapi.com/docs/google-lens-api
        params = {
            "engine": "google_lens",
            "api_key": api_key
        }
        
        # Prepare multipart form data with image
        files = {
            "image": (os.path.basename(image_path), image_data)
        }
        
        print("  → Sending request to SerpApi Google Lens...")
        
        response = requests.post(
            "https://serpapi.com/search",
            params=params,
            files=files,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if "error" in data:
            raise Exception(f"SerpApi error: {data['error']}")
        
        # Extract results
        results = data.get("visual_matches", [])
        
        if not results:
            print("  ⚠ No results from SerpApi. Image may not exist online yet.")
            # Save empty result
            output_file = os.path.join(output_dir, "matched_post.json")
            with open(output_file, "w") as f:
                json.dump({
                    "status": "no_results",
                    "message": "No visual matches found from reverse image search",
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
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
        output_file = os.path.join(output_dir, "matched_post.json")
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
