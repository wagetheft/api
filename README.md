# Wage Theft API

This API provides easy access to enforcement data on investigations conducted by the U.S. Department of Labor's Wage and Hour Division. The data is from investigations of companies under laws relating to minimum wage and overtime, child labor protections, prevailing wages on government contracts, family and medical leave, and more. The API can lookup investigations based on company name, location, industry and time period.  It can either return data on individual cases or it can agregate the data to show summary results by location or industry. 

The data used in this API is published in CSV format on the [Department of Labor's web site](https://enforcedata.dol.gov/views/data_catalogs.php). It includes data on concluded cases as far back as fiscal year 2005.

## Synopsis

[/api/v1/cases?state=CA&city=Oakland](http://stopwagetheft.stanford.edu/api/v1/cases?state=CA&city=Oakland)

[/api/v1/cases?state=CA&county=Alameda%20County&dates=2012& industry=Construction&return_format=html](http://stopwagetheft.stanford.edu/api/v1/cases?state=CA&county=Alameda%20County&dates=2012&industry=Construction&return_format=html)

[/api/v1/cases?company_name=CVS&dates=2010,2017& columns=legal_name,trade_name,city,state,backwages& return_format=googledatatable](http://stopwagetheft.stanford.edu/api/v1/cases?company_name=CVS&dates=2010,2017&columns=legal_name,trade_name,city,state,backwages&return_format=googledatatable)

[/api/v1/cases?columns=sum(minimum_wage_backwages),naics4_description, cases_count&industry=Restaurants&state=FL& order=minimum_wage_backwages%20desc&return_format=csv](http://stopwagetheft.stanford.edu/api/v1/cases?columns=sum\(minimum_wage_backwages\),naics4_description,cases_count&industry=Restaurants&state=FL&order=minimum_wage_backwages%20desc&return_format=csv)

[/api/v1/cases?company_name=CVS&dates=2011-10-01,2017-05-12&columns=legal_name,trade_name,city,state,backwages& return_format=googledatatable](http://stopwagetheft.stanford.edu/api/v1/cases?company_name=CVS&dates=2011-10-01,2017-05-12&columns=legal_name,trade_name,city,state,backwages&return_format=googledatatable)

[/api/v1/cases?columns=all&where=minimum_wage_backwages>1400000](http://stopwagetheft.stanford.edu/api/v1/cases?columns=all&where=minimum_wage_backwages>1400000)
