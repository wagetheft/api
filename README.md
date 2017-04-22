# Wage Theft API

This API provides easy access to enforcement data on investigations conducted by the U.S. Department of Labor's Wage and Hour Division. The data is from investigations of companies under laws relating to minimum wage and overtime, child labor protections, prevailing wages on government contracts, family and medical leave, and more. The API can lookup investigations based on company name, location, industry and time period.  It can either return data on individual cases or it can agregate the data to show summary results by location or industry. 

The data used in this API is published in CSV format on the [Department of Labors web site](https://enforcedata.dol.gov/views/data_catalogs.php). It includes data on concluded cases as far back as fiscal year 2005.

## Synopsis

[/api/v1/cases?state=CA&city=Oakland](http://stopwagetheft.stanford.edu/api/v1/cases?state=CA&city=Oakland)

[/api/v1/cases?state=CA&county=Alameda%20County&dates=2012& industry=Construction&return_format=html](http://stopwagetheft.stanford.edu/api/v1/cases?state=CA&county=Alameda%20County&dates=2012&industry=Construction&return_format=html)

[/api/v1/cases?company_name=CVS&dates=2010,2017& columns=legal_name,trade_name,city,state,backwages& return_format=googledatatable](http://stopwagetheft.stanford.edu/api/v1/cases?company_name=CVS&dates=2010,2017&columns=legal_name,trade_name,city,state,backwages&return_format=googledatatable)

[/api/v1/cases?columns=sum(minimum_wage_backwages),naics4_description, cases_count&industry=Restaurants&state=FL& order=minimum_wage_backwages%20desc&return_format=csv](http://stopwagetheft.stanford.edu/api/v1/cases?columns=sum\(minimum_wage_backwages\),naics4_description,cases_count&industry=Restaurants&state=FL&order=minimum_wage_backwages%20desc&return_format=csv)

[/api/v1/cases?company_name=CVS&dates=2011-10-01,2017-05-12&columns=legal_name,trade_name,city,state,backwages& return_format=googledatatable](http://stopwagetheft.stanford.edu/api/v1/cases?company_name=CVS&dates=2011-10-01,2017-05-12&columns=legal_name,trade_name,city,state,backwages&return_format=googledatatable)

[/api/v1/cases?columns=all&where=minimum_wage_backwages>1400000](http://stopwagetheft.stanford.edu/api/v1/cases?columns=all&where=minimum_wage_backwages>1400000)

## Filtering

You can filter the investiations returned using any combination of these query parameters:
* state - example: `cases?state=FL`
* county - example: `cases?county=Alameda%20County`
* city - example: `cases?city=Miami`
* state_fips_code
* state_county_code
* industry - [list of all industries](http://stopwagetheft.stanford.edu/api/v1/cases?columns=sum(backwages),industry&return_format=html&order=industry%20asc)
* company_name
* dates - examples:
** All cases in 2014: `cases?dates=2014`
** All cases between 2012 and 2014: `cases?dates=2012,2014`
** All cases between 10/1/2013 and 9/30/2014: `cases?dates=2013-10-1,2014-9-30`

The company_name parameter does a full text search on both trade_name and legal_name. Industry also performs a full text search. Other fields like state, county, and city must be an exact match. That means `cases?county=Alameda` will not return any results. Instead you must use `cases?county=Alameda%20County`.

INSERT DESCRIPTION OF HOW TO USE WHERE HERE

## Available Fields

* case_id: Case ID used by the U.S. Department of Labor for the investigation of this business
* trade_name: business trade name
* legal_name:  business legal name
* street_address:  street address of the business
* city:  city of the business
* state:  state of the business
* zip: zip of the business
* county:  county of the business
* county_fips_code:  county FIPS code where the business is located
* state_fips_code:  state FIPS code where the business is located
* combined_state_county_fips:  combined state and county FIPS code
* latitude: latitude for the address
* longitude: longitude for the address
* backwages: total back wages owed to workers
* employees_owed_backwages: number of employees owed back wages
* civil_money_penalties:  civil money penalty assessed against the company
* findings_start_date:  start date for the period of time the investigation covered
* findings_end_date:  end date for the period of time the investigation covered
* industry: a custom non-DOL categorization by industry based on the NAICS code for easy access - see below for more on the NAICS codes
* full_naics_code: the full NAICS code reported by DOL
* full_naics_description:  the full NAICS code description from DOL
* naics2:  the left 2 digits of the NAICS code
* naics2_description:  the description for the first 2 digits of the NAICS code from the 1997 NAICS descriptions 
* naics3:  the left 3 digits of the NAICS code
* naics3_description:  the description for the first 3 digits of the NAICS code from the 1997 NAICS descriptions
* naics4:  the left 4 digits of the NAICS code
* naics4_description:  the description for the first 4 digits of the NAICS code from the 1997 NAICS descriptions
* minimum_wage_and_overtime_backwages: minimum wage and overtime backwages - only applies to Fair Labor Standards Act (FLSA) cases
* employees_owed_minimum_wage_and_overtime_backwages: number of employees owed minimum wage and overtime backwages - only applies to FLSA cases 
* minimum_wage_backwages:  minimum wage backwages - only applies to FLSA cases
* overtime_backwages:  overtime backwages - only applies to FLSA cases
* retaliation_backwages:  Retaliation Backwages,
* cases_count:  this field can only be used when grouping results using sum or avg as it returns the number of cases for each group of results

### Requesting Specific Fields
The API returns these fields by default: case_id, trade_name, legal_name, street_address, city, state, zip, latitude, longitude, industry, backwages, employees_owed_backwages, civil_money_penalties, findings_start_date, and findings_end_date.

To return all fields, use columns=all. Example: `cases?columns=all`

To return a specific subset of fields, substitite a list of columns for 'all'. Example: `cases?columns=legal_name,backwages,industry`


### NAICS
The NAICS code is an industry standard for describing industries. The first 2 digits of the code define the overall industry. For example, 23 is Construction. Each additional digit describes a lower level of industry grouping. So, 236 is Construction of Buildings and 237 is Heavy and Civil Engineering Construction, and 2361 is Residential Building Construction and 2362 is Nonresidential Building Construction. Unfortunately, in the DOL database not all digits of the NAICS code are filled in on every investigation. They are consistently filled in to at least the 4th digit. For that reason, the API only provides the NAICS broken down by 2, 3, and 4 digits. However, the full NAICS code is also provided which might be 4, 5 or 6 digits. If you use the full NAICS your code just has to be able to handle a NAICS with an unknown number of digits.

Data to illustrate from the API:
* [Full list of NAICS 2](http://stopwagetheft.stanford.edu/api/v1/cases?columns=sum(backwages),naics2,naics2_description&return_format=html&order=naics2%20asc)
* [Full list of NAICS 3](http://stopwagetheft.stanford.edu/api/v1/cases?columns=sum(backwages),naics3,naics3_description&return_format=html&order=naics3%20asc)
* [Full list of NAICS 4](http://stopwagetheft.stanford.edu/api/v1/cases?columns=sum(backwages),naics4,naics4_description&return_format=html&order=naics4%20asc)


The NAICS descriptions are not always user friendly and the groupings do not allow easy access to the most common industries with wage violations. For that reason we have created a custom "industry" field which uses the NAICS codes to come up with logical groupings. 

Data to illustrate from the API:
* [full list of industries](http://stopwagetheft.stanford.edu/api/v1/cases?columns=sum(backwages),industry&return_format=html&order=industry%20asc).


## Return Format of Data

By default the API returns data in the JSON format. However, using the return_format parameter you can tell the API to return data in other formats. These include:
* csv - a text file with comma separated values.
* html - this is most useful to developers who want to be able to tell what results a specific API call would produce.
* googledatatable - this returns the data in a JSON format already formatted properly to create a Google DataTable for use by Google Maps or Charts API. 

Examples:
* `cases?return_format=csv`
* `cases?return_format=html`
* `cases?return_format=googledatatable`

### Callback Function
By default the API returns a data structure that is not wrapped in a callback function. However, it wrap the data in a callback function if you specify the name of the callback function using the callback parameter. Example: `cases?callback=my_callback_function`

