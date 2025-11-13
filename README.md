# Election Results Mapper

[Click here to view the example map for Saguenay Lac-Saint-Jean](https://carlouellette.ca/saglac_polls/saglac_polls.html)

### Overview
This project creates interactive maps of Canadian federal election results at the polling division level. It combines Elections Canada data with geographic boundaries to visualize voting patterns.

### Prerequisites
- Python 3.7+
- Required Python packages: `geopandas`, `pandas`

### Installation
```bash
pip install geopandas pandas
```

### Step-by-Step Guide

#### 1. Download Election Results Data
- Go to: [Poll-by-poll Results, by Electoral District](https://www.elections.ca/content.aspx?section=res&dir=rep/off/45gedata&document=byed&lang=e)
- Download the CSV file for your desired electoral district
- Files are named like: `pollbypoll_bureauparbureauXXXXX.csv` (where XXXXX is the district number)

#### 2. Download Polling Division Boundaries
- Go to: [Electoral Geography Boundary Files](https://www.elections.ca/content.aspx?section=res&dir=cir/mapsCorner/vector&document=index&lang=e)
- Download the "Polling Division Boundaries - Shapefile" ZIP file
- Extract the contents to your project folder (you should get files like `PD_CA_2025_EN.shp`)

#### 3. Convert Shapefile to GeoJSON
Run the conversion script first:

```bash
python togeojson.py
```

This creates `polling_divisions.geojson` from the shapefile.

#### 4. Process the Election Data
Run the main processing script to merge election results with geographic boundaries:

```bash
python filtergeojson.py pollbypoll_bureauparbureauXXXXX.csv
```

Replace `XXXXX` with your district number.

**Optional parameters:**
```bash
python filtergeojson.py pollbypoll_bureauparbureauXXXXX.csv polling_divisions.geojson your_district_name
```

#### 5. Update the HTML File
The script will generate two files:
- `[district]_election_results.geojson` (complete data)
- `[district]_election_simple.geojson` (optimized for web)

Add your district to the HTML dropdown in `saglac_polls.html`:
```html
<select id="datasetSelect">
    <option value="your_district_election_simple.geojson">Your District Name</option>
    <!-- Existing options -->
</select>
```
Optionally, you can update the candidate colors in the HTML file:
```javascript
const partyColors = {
    "Candidate Name": "#XXXXXX",
    // Existing party colors
}
```

#### 6. View the Map
When opening the HTML file directly in a browser, you may encounter CORS (Cross-Origin Resource Sharing) errors that prevent the GeoJSON files from loading.  
To resolve this, you can start a local server and open the map:
```bash
python -m http.server 8000
```
Then visit [http://localhost:8000/saglac_polls.html](http://localhost:8000/saglac_polls.html) or your new HTML file in your browser

### Complete Workflow Example
#### 1. Convert shapefile to GeoJSON
```bash
python togeojson.py
```

#### 2. Process election data for district 24030
```bash
python filtergeojson.py pollbypoll_bureauparbureau24030.csv
```

#### 3. Update the HTML file with your new district
```html
<select id="datasetSelect">
    <option value="pollbypoll_bureauparbureau24030_election_simple.geojson">Jonquière</option>
    <!-- Existing options -->
</select>
```

#### 4. Open the HTML file in your browser
```bash
python -m http.server 8000
```
Then visit [http://localhost:8000/saglac_polls.html](http://localhost:8000/saglac_polls.html) or your own HTML file in your browser

### File Structure
```
project/
├── togeojson.py              # Shapefile to GeoJSON converter
├── filtergeojson.py          # Data processing script
├── saglac_polls.html         # Main web interface
├── PD_CA_2025_EN.*           # Original shapefile components
├── polling_divisions.geojson # Converted boundaries
├── pollbypoll_bureauparbureauXXXXX.csv  # Election results
└── *_election_simple.geojson # Generated map data
```
