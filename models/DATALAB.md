# Datalab.to API Documentation

## General Info

These hosted APIs leverage the [surya](https://github.com/VikParuchuri/surya) and [marker](https://github.com/VikParuchuri/marker) projects to do OCR, convert PDFs to markdown, and recognize tables.

## Billing

Your initial plan gives you a certain number of credits. Each request will cost a certain amount, rounded up to the nearest cent. You can see the per-page prices on the plans page. If you go above the initial credit, you will be billed for the overage.

## Authentication

You authenticate by setting the `X-Api-Key` header. You can find your API keys in the dashboard. Billing limits can be set per-key to avoid high bills.

## Limits

### Rate Limits

The request limit for all endpoints is **200** per **60** seconds. You also cannot have more than **200** concurrent requests. You'll get a `429` error if you exceed the rate limit.

Reach out to `support@datalab.to` if you need higher limits.

### File Size Limits

The file size limit for all endpoints is **200MB** currently. If you need to submit larger files, please reach out to `support@datalab.to`. One solution is also to slice the file into chunks that are under **200MB** in size.

## Callbacks

You will normally need to poll to get API results. If you don't want to poll, you can specify a URL that will be hit when inference is complete. Specify the webhook URL in the settings panel on the dashboard.

The callback will pass this data to your webhook URL:

- `request_id` - lookup key of the original request
- `webhook_secret` - a webhook secret you can define to reject other messages
- `request_check_url` - the url you will need to hit to get the full results

---

# API Endpoints

All endpoints will return immediately, and continue processing in the background.

## Marker

The marker endpoint converts PDFs, spreadsheets, word documents, epub, HTML, and powerpoints to markdown. It is available at `/api/v1/marker`.

### Example Request

```python
import requests

url = "https://www.datalab.to/api/v1/marker"

form_data = {
    'file': ('test.pdf', open('~/pdfs/test.pdf', 'rb'), 'application/pdf'),
    "force_ocr": (None, False),
    "paginate": (None, False),
    'output_format': (None, 'markdown'),
    "use_llm": (None, False),
    "strip_existing_ocr": (None, False),
    "disable_image_extraction": (None, False)
}

headers = {"X-Api-Key": "YOUR_API_KEY"}

response = requests.post(url, files=form_data, headers=headers)
data = response.json()
```

As you can see, everything is a form parameter. This is because we're uploading a file, so the request body has to be `multipart/form-data`.

### Parameters

- `file` - the input file
- `output_format` - one of `json`, `html`, or `markdown`
- `force_ocr` - will force OCR on every page (ignore the text in the PDF). This is slower, but can be useful for PDFs with known bad text
- `format_lines` - will partially OCR the lines to properly include inline math and styling (bold, superscripts, etc.). This is faster than `force_ocr`
- `paginate` - adds delimiters to the output pages
- `use_llm` - setting this to `True` will use an LLM to enhance accuracy of forms, tables, inline math, and layout. It can be much more accurate, but carries a small hallucination risk. Setting `use_llm` to `True` will make responses slower
- `strip_existing_ocr` - setting to `True` will remove all existing OCR text from the file and redo OCR. This is useful if you know OCR text was added to the PDF by a low-quality OCR tool
- `disable_image_extraction` - setting to `True` will disable extraction of images. If `use_llm` is set to `True`, this will also turn images into text descriptions
- `max_pages` - from the start of the file, specifies the maximum number of pages to inference

### Initial Response

The request will return the following:

```json
{
    "success": true,
    "error": null,
    "request_id": "PpK1oM-HB4RgrhsQhVb2uQ",
    "request_check_url": "https://www.datalab.to/api/v1/marker/PpK1oM-HB4RgrhsQhVb2uQ"
}
```

### Polling for Results

You will then need to poll `request_check_url`, like this:

```python
import time

max_polls = 300
check_url = data["request_check_url"]

for i in range(max_polls):
    time.sleep(2)
    response = requests.get(check_url, headers=headers)  # Don't forget to send the auth headers
    data = response.json()

    if data["status"] == "complete":
        break
```

### Final Response

You can customize the max number of polls and the check interval to your liking. Eventually, the `status` field will be set to `complete`, and you will get an object that looks like this:

```json
{
    "output_format": "markdown",
    "markdown": "...",
    "status": "complete",
    "success": true,
    "images": {...},
    "metadata": {...},
    "error": "",
    "page_count": 5
}
```

If success is `False`, you will get an error code along with the response.

All response data will be deleted from datalab servers an hour after the processing is complete, so make sure to get your results by then.

### Response Fields

- `output_format` - the requested output format: `json`, `html`, or `markdown`
- `markdown` | `json` | `html` - the output from the file. It will be named according to the `output_format`
- `status` - indicates the status of the request (`complete`, or `processing`)
- `success` - indicates if the request completed successfully. `True` or `False`
- `images` - dictionary of image filenames (keys) and base64 encoded images (values). Each value can be decoded with `base64.b64decode(value)`
- `metadata` - metadata about the markdown conversion
- `error` - if there was an error, this contains the error message
- `page_count` - number of pages that were converted

### Supported File Types

Marker supports the following extensions and mime types:

- **PDF** - `pdf`/`application/pdf`
- **Spreadsheet** - `xls`/`application/vnd.ms-excel`, `xlsx`/`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `ods`/`application/vnd.oasis.opendocument.spreadsheet`
- **Word document** - `doc`/`application/msword`, `docx`/`application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `odt`/`application/vnd.oasis.opendocument.text`
- **Powerpoint** - `ppt`/`application/vnd.ms-powerpoint`, `pptx`/`application/vnd.openxmlformats-officedocument.presentationml.presentation`, `odp`/`application/vnd.oasis.opendocument.presentation`
- **HTML** - `html`/`text/html`
- **Epub** - `epub`/`application/epub+zip`
- **Images** - `png`/`image/png`, `jpeg`/`image/jpeg`, `webp`/`image/webp`, `gif`/`image/gif`, `tiff`/`image/tiff`, `jpg`/`image/jpg`

You can automatically find the mimetype in python by installing `filetype`, then using `filetype.guess(FILEPATH).mime`.

### Troubleshooting

If you get bad output, setting `format_lines` or `force_ocr` to `True` is a good first step. A lot of PDFs have bad text inside. Marker attempts to auto-detect this and run OCR, but the auto-detection is not 100% accurate.

---

## Table Recognition

The table recognition endpoint at `/api/v1/table_rec` will detect tables, then identify the structure and format the tables properly.

### Example Request

```python
import requests

url = "https://www.datalab.to/api/v1/table_rec"

form_data = {
    'file': ('test.png', open('~/images/test.png', 'rb'), 'image/png'),
}

headers = {"X-Api-Key": "YOUR_API_KEY"}

response = requests.post(url, files=form_data, headers=headers)
data = response.json()
```

The api accepts files of type `application/pdf`, `image/png`, `image/jpeg`, `image/webp`, `image/gif`, `image/tiff`, and `image/jpg`.

### Optional Parameters

- `max_pages` - lets you specify the maximum number of pages of a pdf to make predictions for
- `skip_table_detection` - doesn't re-detect tables if your pages are already cropped
- `detect_cell_boxes` - will re-detect all cell bounding boxes vs using the text in the PDF
- `output_format` - the format of the output, one of `markdown`, `html`, `json`. Default is `markdown`
- `paginate` - determines whether to paginate markdown output. Default is `False`
- `use_llm` - optionally uses an LLM to merge tables and improve accuracy. This can be much more accurate, but has a small hallucination risk. It also doubles the per-page cost. Setting `use_llm` to `True` will make responses slower

### Response

The polling process is the same as the Marker endpoint. The final response will look like this:

```json
{
    "output_format": "markdown",
    "markdown": "...",
    "status": "complete",
    "success": true,
    "metadata": {...},
    "error": "",
    "page_count": 5
}
```

### Response Fields

- `output_format` - the requested output format: `json`, `html`, or `markdown`
- `markdown` | `json` | `html` - the output from the file
- `status` - indicates the status of the request (`complete`, or `processing`)
- `success` - indicates if the request completed successfully. `True` or `False`
- `metadata` - metadata about the markdown conversion
- `error` - if there was an error, this contains the error message
- `page_count` - number of pages that were converted

---

## OCR

The OCR endpoint at `/api/v1/ocr` will OCR a given pdf, word document, powerpoint, or image.

### Example Request

```python
import requests

url = "https://www.datalab.to/api/v1/ocr"

form_data = {
    'file': ('test.png', open('~/images/test.png', 'rb'), 'image/png'),
}

headers = {"X-Api-Key": "YOUR_API_KEY"}

response = requests.post(url, files=form_data, headers=headers)
data = response.json()
```

The api accepts files of type `application/pdf`, `image/png`, `image/jpeg`, `image/webp`, `image/gif`, `image/tiff`, and `image/jpg`. The optional parameter `max_pages` lets you specify the maximum number of pages of a pdf to make predictions for.

### Response

The polling process is the same as other endpoints. The final response will look like this:

```json
{
    "status": "complete",
    "pages": [
        {
            "text_lines": [{
                "polygon": [[267.0, 139.0], [525.0, 139.0], [525.0, 159.0], [267.0, 159.0]],
                "confidence": 0.99951171875,
                "text": "Subspace Adversarial Training",
                "bbox": [267.0, 139.0, 525.0, 159.0]
            }, ...],
            "image_bbox": [0.0, 0.0, 816.0, 1056.0],
            "page": 12
        }
    ],
    "success": true,
    "error": "",
    "page_count": 5
}
```

### Response Fields

- `status` - indicates the status of the request (`complete`, or `processing`)
- `success` - indicates if the request completed successfully. `True` or `False`
- `error` - If there was an error, this is the error message
- `page_count` - number of pages we ran ocr on
- `pages` - a list containing one dictionary per input page. The fields are:
  - `text_lines` - the detected text and bounding boxes for each line
    - `text` - the text in the line
    - `confidence` - the confidence of the model in the detected text (0-1)
    - `polygon` - the polygon for the text line in (x1, y1), (x2, y2), (x3, y3), (x4, y4) format. The points are in clockwise order from the top left
    - `bbox` - the axis-aligned rectangle for the text line in (x1, y1, x2, y2) format. (x1, y1) is the top left corner, and (x2, y2) is the bottom right corner
    - `chars` - the individual characters in the line
      - `text` - the text of the character
      - `bbox` - the character bbox (same format as line bbox)
      - `polygon` - the character polygon (same format as line polygon)
      - `confidence` - the confidence of the model in the detected character (0-1)
      - `bbox_valid` - if the character is a special token or math, the bbox may not be valid
  - `page` - the page number in the file
  - `image_bbox` - the bbox for the image in (x1, y1, x2, y2) format. (x1, y1) is the top left corner, and (x2, y2) is the bottom right corner. All line bboxes will be contained within this bbox

---

## Layout

The layout endpoint at `/api/v1/layout` will detect layout bboxes in a given pdf, word document, powerpoint, or image. The possible labels for the layout bboxes are: `Caption`, `Footnote`, `Formula`, `List-item`, `Page-footer`, `Page-header`, `Picture`, `Figure`, `Section-header`, `Table`, `Text`, `Title`. The layout boxes are then labeled with a `position` field indicating their reading order, and sorted.

### Example Request

```python
import requests

url = "https://www.datalab.to/api/v1/layout"

form_data = {
    'file': ('test.png', open('~/images/test.png', 'rb'), 'image/png'),
}

headers = {"X-Api-Key": "YOUR_API_KEY"}

response = requests.post(url, files=form_data, headers=headers)
data = response.json()
```

The api accepts files of type `application/pdf`, `image/png`, `image/jpeg`, `image/webp`, `image/gif`, `image/tiff`, and `image/jpg`. The optional parameter `max_pages` lets you specify the maximum number of pages of a pdf to make predictions for.

### Response

The polling process is the same as other endpoints. The final response will look like this:

```json
{
    "status": "complete",
    "pages": [
        {
            "bboxes": [
                {
                    "bbox": [0.0, 0.0, 1334.0, 1625.0],
                    "position": 0,
                    "label": "Table",
                    "polygon": [[0, 0], [1334, 0], [1334, 1625], [0, 1625]]
                }
            ],
            "image_bbox": [0.0, 0.0, 1336.0, 1626.0],
            "page": 1
        }
    ],
    "success": true,
    "error": "",
    "page_count": 5
}
```

### Response Fields

- `status` - indicates the status of the request (`complete`, or `processing`)
- `success` - indicates if the request completed successfully. `True` or `False`
- `error` - If there was an error, this is the error message
- `page_count` - number of pages we ran layout on
- `pages` - a list containing one dictionary per input page. The fields are:
  - `bboxes` - detected layout bounding boxes
    - `bbox` - the axis-aligned rectangle for the text line in (x1, y1, x2, y2) format. (x1, y1) is the top left corner, and (x2, y2) is the bottom right corner
    - `polygon` - the polygon for the text line in (x1, y1), (x2, y2), (x3, y3), (x4, y4) format. The points are in clockwise order from the top left
    - `label` - the label for the bbox. One of `Caption`, `Footnote`, `Formula`, `List-item`, `Page-footer`, `Page-header`, `Picture`, `Figure`, `Section-header`, `Table`, `Text`, `Title`
    - `position` - the reading order of this bbox within the page
  - `page` - the page number in the input file
  - `image_bbox` - the bbox for the page image in (x1, y1, x2, y2) format. (x1, y1) is the top left corner, and (x2, y2) is the bottom right corner. All layout bboxes will be contained within this bbox

---

## Important Notes

- All response data will be deleted from datalab servers an hour after the processing is complete, so make sure to get your results by then
- If success is `False`, you will get an error code along with the response
- All endpoints support the same file types as listed in the Marker section
- Contact `support@datalab.to` for questions or if you need higher limits