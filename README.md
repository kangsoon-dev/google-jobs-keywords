# Technical skills counter for job postings from Google Search
Scrapes jobs and their descriptions from Google Job Search according to the search term specified and a CSV file containing the keywords to search for in the description. Returns the frequency list for each keyword. Spaces and special characters are allowed in the keyword term.

# Installation
The following Python libraries should be installed (with pip, or the package manager of your choice):
- Selenium
- Pandas

Please also ensure that your version of Chromedriver is compatible with the browser version on your computer/machine. If required, please replace the file in this repository with a compatible version.

[Chromedriver](https://sites.google.com/chromium.org/driver/)

# Usage
The script can be run from the command line using: <code>$python3 scrape_jobs.py [commands]</code>

<code>
$ python3 scrape_jobs.py 
usage: scrape_jobs.py [--search_term] [--limit] [--is_today]

  -search_term  Search term to find in Google Job Search

  -limit        Maximum number of jobs to return from search
                
  -is_today     Indicates whether to return results posted only from the last 24 hours.

</code>
