#!/usr/bin/env python

# ++++++ Python Version ++++++
# This program is only tested with Python 3. 

# +++++ Note from Michael +++++
# This code is not fully documented - apologies for that. I will continue working on fully 
# documenting everything. This is my first program in Python so I'm sure there are various
# places where I could have done things differently/better. Feel free to refactor/tweak to 
# correct my errors.

# ++++++Known issues++++++++
# I have not fully tested all of the user input to prevent Sqlinjection attacks. I
# believe I have marked the user inputs that have not been properly screened for 
# injection attacks but ideally someone else would go back over everything else.
#from json import dumps

from flask import Flask, make_response, request, Response, redirect, current_app, render_template

from flask_restful import Resource, Api, reqparse, abort

# note from Michael: the code uses direct SQL queries so sqlalchemy may not be needed. However, the create_engine
# command is used to connect to the database and I didn't get around to looking up how to do this
# without using sqlalchemy
from sqlalchemy import create_engine


# Cashing in Flask is not enabled but we could consider adding this as a feature later.
# enable caching
#from flask.ext.cache import Cache

# needed for proper formatting of dates into JSON
from flask.json import JSONEncoder

# In theory this is to make it compatible with Python 2 and 3. However, the code is only
# test on Python 3 so maybe we simplify this and make Python 3 required?
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO        
        

import csv

# Using simplejson because json does not allow converting decimals to numbers
import simplejson

# The API assumes that the config file is in the same folder as this script
with open('api-config.json', 'r') as f:
    config = simplejson.load(f)
    
# Create the connection string from our config file for connecting to the database
d = config['database'] 
connection_string = d['type'] +'://' + d['username'] + ":" + d['password'] + "@" + d['host'] + "/" + d['name']

# Create an engine for connecting to postgreSQL
e = create_engine(connection_string)

# These are used to print out pretty column headers when the user specifies that they want 
# the data returned in HTML format.
column_labels= {
    'case_id': 'Case ID',
    'trade_name': 'Trade Name',
    'legal_name': 'Legal Name',
    'street_address': 'Street Address',
    'city': 'City',
    'state':'State',
    'zip':'Zip',
    'latitude':'Latitude',
    'longitude':'Longitude',
    'backwages':'Backwages',
    'employees_owed_backwages':'Employees Owed Backwages',
    'civil_money_penalties': 'Civil Money Penalties',
    'findings_start_date': 'Findings Start Date',
    'findings_end_date': 'Findings End Date',
    'county': 'County',
    'county_fips_code': 'County FIPS Code',
    'state_fips_code': 'State FIPS Code',
    'combined_state_county_fips': 'Combined State County_fips',
    'industry': 'Industry',
    'full_naics_code': 'Full NAICS Code',
    'full_naics_description': 'Full NAICS Description',
    'naics2': 'NAICS2',
    'naics2_description': 'Industry',
    'naics3': 'NAICS3',
    'naics3_description': 'Industry',
    'naics4': 'NAICS4',
    'naics4_description': 'Industry',
    'minimum_wage_and_overtime_backwages': 'Minimum Wage and Overtime Backwages',
    'employees_owed_minimum_wage_and_overtime_backwages': 'Employees Owed Minimum Wagea and Overtime Backwages',
    'minimum_wage_backwages': 'Minimum Wage Backwages',
    'overtime_backwages': 'Overtime Backwages',
    'retaliation_backwages': 'Retaliation Backwages',
    'cases_count': "Number of Cases"
}


# This is a list of all the columns that are returned by default if the user does not specify
# which columns to return.
columns_default = "case_id, trade_name, legal_name, street_address, city, state, zip, latitude, longitude, industry, backwages, employees_owed_backwages, civil_money_penalties, findings_start_date, findings_end_date"


# These are the additional columns that are available besides the decault columns
columns_additional = "county, state_fips_code, county_fips_code, combined_state_county_fips, full_naics_code, full_naics_description, naics2, naics2_description, naics3, naics3_description, naics4, naics4_description,  minimum_wage_and_overtime_backwages, employees_owed_minimum_wage_and_overtime_backwages, minimum_wage_backwages, overtime_backwages, retaliation_backwages"

# columns_all as the name suggests contains all of the columns, both default and additional
columns_all = columns_default + ", " + columns_additional

# Here is the same list of columns but this time split into an actual list. 
columns_all_list = [x.strip() for x in columns_all.split(',')]

# Create the Flask app
app = Flask(__name__)
api = Api(app)


# register the cache instance and binds it on to the app 
#cache = Cache(app,config={'CACHE_TYPE': 'simple'})

# These are all the optional parameters that can be given to the API
parser = reqparse.RequestParser(bundle_errors=True)

#
parser.add_argument('return_format', type=str, help='by default the API returns JSON. However, you can specify either csv, googledatatable, or html as alternate formats.')

# The company name parameter is used to do a full text search on both the legal_name and trade_name fields.
# This is the best way to search for a company by name.
parser.add_argument('company_name', type=str)

# If the columns  parameter is not supplied, the default list of columns is returned (see the list above). 
# Alternatively, the user can either supply a comma separated list of columns, or can specify all 
# to return all columns. One special column is available when grouping results:  cases_count
# cases_count returns the number of cases included in that group, so for example if grouping by 
# city, cases_count would return the number of cases for each city.
parser.add_argument('columns', type=str)


# The where parameter allows the user to insert a where clause. The user must use the format where=column='STRING'
# The ' characters must be URL escaped properly. The user can also do things like where=column is not null.
# The backend is Postgres and the where clause is just passed on directly to the server. That brings us to this:
# SQL INJECTION RISK: this column has not been properly escaped. We need to figure out a way to properly
# escape it.
parser.add_argument('where', type=str)


# Use offset to start the record request not at record 1 but instead at a certain number of records in 
# specififed by the number supplied.
parser.add_argument('offset', type=int, help='The value given for offset must be a number')

# This is another name for offset
parser.add_argument('start', type=int, help='The value given for start must be a number') 

# Limits the total number of records returned
parser.add_argument('limit', type=int, help='The value given for limit must be a number')

# This is another name for limit
parser.add_argument('length', type=int, help='The value given for length must be a number') 

# Set the returned set to be ordered by a column using the order parameter.
# order=backwages DESC
# order=bacwages ASC
parser.add_argument('order', type=str)

# DEPRECATED. This used to be use to manually state what columns are being grouped on.
# Now the parser recognizes if an aggregating function is being used like sum() and if so then 
# it automatically groups by the columns requested that no aggregating functions are applied to.
parser.add_argument('group', type=str)

# Search by the 2 digit state code (i.e. CA, MN, etc.). This is an easier way to limit the return
# results than using the where parameter. Instead of doing where=state='CA' the user can instead 
# just say state=CA

parser.add_argument('state', type=str)

# Searech by county (you must inclulde County so for Santa Clara you would use county=Santa Clara)
parser.add_argument('county', type=str)


# Search by city
parser.add_argument('city', type=str)

# Search by state FIPS code
parser.add_argument('state_fips_code', type=int, help='The value given for the state_fips_code must be a number')

# Search by County FIPS code
parser.add_argument('county_fips_code', type=int, help='The value given for county_fips_code must be a number')

# Search by Industry. This is a custom industry description that is more human readable than the NAICS
# industry codes and also breaks the cases out in more logical categories. 
parser.add_argument('industry', type=str)


# This identifies the request number which is important when the requestor may be making multiple requests so
# the requestor can identify which response it is. J-query DataTables uses this.
parser.add_argument('draw', type=int, help='The value given for draw must be a number') 



# This code is necessary to format the json responses using simplejson instead of regular json
# which is needed due to the fact that regular json does not handle decimal numbers correctly
# and triggers an error when loading our data which has decimal numbers in it.
@api.representation('application/json')
def output_json(data, code, headers=None):
    
    #'This is needed for J-query DataTables when multiple requests are being made to distinguish between requests
    draw = 0
    if 'draw' in request.args:
        draw = request.args['draw']
    data['draw'] = draw
    
    if 'callback' in request.args:
        # The user supplied a callback function name so return JSONP with the data wrapped in the supplied
        # function name instead of straight JSON
        
        callback_function_name = request.args['callback']
        resp = make_response(callback_function_name + "("+simplejson.dumps(data, cls = CustomEncoder)+")", code)
    else:
        
        resp = make_response(simplejson.dumps(data, cls = CustomEncoder), code)
        
    resp.headers.extend(headers or {})
        
    return resp


# This class makes dates work. Otherwise without this code, simplejson dies with an error if 
# a date column is included.
# THIS CODE ONLY RUNS ON DATE OBJECTS. CAN'T FIGURE OUT WHY. THIS IS PREVENTING
# THE ADDITION OF CUSTOM CODE TO GET RID OF THE .0 AFTER ZIP CODES
class CustomEncoder(simplejson.JSONEncoder):
    def default(self, obj):

        # WAS USING TO SEE WHAT OBJECTS WERE BEING RUN THROUGH HERE BY SIMPLEJSON.
        # ANSWER: ONLY DATES. WHY?
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(obj)


        try:
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()

        except TypeError:
            pass
        else:
            return list(iterable)


        return simplejson.JSONEncoder.default(self, obj)


        # POSSIBLE CODE TO HELP WITH RECOGNIZING ZIP CODES ONCE WE GET THIS SECTION TO
        # RUN ON OBJECTS OTHER THAN DATES.

        # if isinstance(obj, decimal.Decimal):
        #     return str(obj)
        # else:
        #     return JSONEncoder.default(self, obj)




# Add support for CORS protocol to allow for AJAX requests from other domains. 
@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET') # PUT,POST,DELETE not included
  return response



# +++++ CaseList Function +++++
# This is the main function that does the majority of the work. It figures out which columns the user wants,
# how the user wants to group and order the columns, and which rows of data to return. It then pulls 
# the requested data from the Postgres database and returns the list of cases or grouped information based on 
# the cases in the format specified by the user.

class CaseList(Resource):
    def get(self):


        args = parser.parse_args()

        # Create the SELECT and GROUP BY parts of the SQL query based on the optional 'columns' argument

        (sql_string_select, sql_string_group, user_columns) = create_sql_select_and_group_strings(safe_arg('columns'))


        # Create the WHERE part of the SQL query

        (sql_string_where, sql_params) = create_sql_where_string( 
            {
                'state': safe_arg('state'), 'state_fips_code': safe_arg('state_fips_code'), 'city': safe_arg('city'), 
                'county': safe_arg('county'), 'county_fips_code': safe_arg('county_fips_code'), 'zip': safe_arg('zip')
            },
            safe_arg('where'), 
            safe_arg('company_name'),
            safe_arg('dates'),
            safe_arg('industry')

        )



        # Build the ORDER BY SQL string
        sql_string_order = ""
        # THIS IS NOT SAFE YET - VULNERABLE TO SQL INJECTIONS
        if 'order' in request.args:
            sql_string_order = " ORDER BY " + request.args['order'] + " "



        # This code reads the special arguments supplied by the Jquery-DataTables library to specify the sort column
        if 'order[0][column]' in request.args:
            # 'order[0][column] if present containts an integer that corresponds to the column number that should be sorted by
            if 'order[0][dir]' in request.args:
                # 'order[0][dir] specifies whether the order is ascending or descending
                order_column_number = request.args['order[0][column]']
                if 'columns[' + order_column_number + '][data]' in request.args:
                    #use the column number to look up the column name, also supplied by the sender
                    sql_string_order = " ORDER BY " + request.args['columns[' + order_column_number + '][data]'] + " " + request.args['order[0][dir]'] + " "


            
        # Build the SQL limit code if either limit or length are set (length is a synonym for limit)
        sql_string_limit = ""
        sql_string_limit_value = -1
        
        # Limit and length should be safe from SQL injections as request.args is configured to only accept an integer as input
        # If limit is not specified, then by default the first 100 records will be returned. However, if the user limits
        # the request by including a where clause, then by default all records will be returned.  If the user wants to force
        # the return of all value, even in the case where there is no where clause, then 0 can be supplied as the limit.
        
        if 'limit' in request.args:
            sql_string_limit_value  = request.args['limit']

        if 'length' in request.args:
            sql_string_limit_value  = request.args['length']
        
        # if still -1, then no value specified. If 0, then user is requesting all rows.
        if sql_string_limit_value  != -1 and str(sql_string_limit_value) != "0":
            
            # User wants a certain number of records
            sql_string_limit= " limit " + str(sql_string_limit_value) + " "
        
        elif len(sql_string_where) == 0 and str(sql_string_limit_value) != "0":
            sql_string_limit =" limit 100 " # FOR NOW ONLY RETURN 100 RECORDS IF NO WHERE CLAUSE EXISTS. OTHERWISE WOULD
            # RETURN THE ENTIRE DATABASE



        # Build the SQL offset code if either offset or start are set (start is a synonym for offset)
        # offset and start should be safe from SQL injections as request.args is configured to only accept an integer as input
        sql_string_offset = ""
        sql_string_offset_value = 0
        
        if 'offset' in request.args:
            sql_string_offset_value  = request.args['offset']

        if 'start' in request.args:
            sql_string_offset_value  = request.args['start']

        if sql_string_offset_value != 0:
            sql_string_offset= " OFFSET " + str(sql_string_offset_value) + " "
        
        
        # Build the full SQL SELECT statement
        sql_string = "SELECT " + sql_string_select + " FROM cases " + sql_string_where + sql_string_group + sql_string_limit + sql_string_offset
        
        sql_string_limit_and_offset = sql_string_limit + sql_string_offset




        # Valid options for the "return_format" parameter include "csv" to return a csv file or "googledatatable" to
        # return a JSON object formatted to be readable directly by the Google Charts Javascript API.
        # By default if "return_format" is not specified, then the data is returned as JSON in a format readable by Jquery-DataTables.
        if 'return_format' in request.args:
            return_format = request.args['return_format']
            return_format = return_format.lower()
        else:
            return_format = "default"
        

        if return_format == "csv":

            csv_string = get_data_csv(sql_query = sql_string, sql_params = sql_params)
            
            return Response(csv_string, mimetype='text/csv')

        else:
            data = get_data(from_table = "cases", limit_and_offset =  sql_string_limit_and_offset,
                            select=sql_string_select, user_columns = user_columns, where=sql_string_where,
                            group = sql_string_group, order= sql_string_order, sql_params = sql_params, return_format=return_format)
            
            if return_format != "html":
                return data

            else:
                return Response(
                    render_template('default.html', data=data['data'], column_labels=column_labels), 
                    mimetype='text/html'
                )   

    
    
    
# +++++ Case Function +++++
# This code currently isn't working.  Efforts went into CaseList not this one. Specific URLs including
# /cases/[case ID] seem like a good idea but we should probably make them be pointers back to the main 
# function with the case ID then set as a parameter. Although currently we do not have the option in the
# main function to limit just to one case_id. So maybe something we need to add in.
class Case(Resource):
    def get(self, case_id=None):

        if (case_id is None):
            abort(409, "Case ID must be given when requesting a specific case. The proper format to request is '/cases/[case id]' replacing '[case id] with the requested case ID.")

        stmt = " select * from cases where case_id=" + str(case_id)
 
        return get_data(sql_query = stmt)



def create_sql_select_and_group_strings(user_columns_string = ""):
    # Valid input for this function includes 'all', 'default', or a list of comma separated column
    # names (i.e. 'backwages,trade_name,state').

    # If "all" is given as the input, then the full column list from the columns_all global will be returned.
    # If "default" is given as the input, then the default column list from the columns_default global will be returned
    # If a comma separated list is given as the input, then this function will parse the list to ensure
    # that each element in the list is a valid column name, or is a column name surrounded by an agregate function
    # such as SUM, AVG, etc..

    # Return format: this function returns two strings and a list. The first string is the list of columns 
    # for the SELECT part of a SQL query. The second string is the GROUP BY part of a SQL query.
    # The last element is a list of columns supplied by the user with any agregate functions removed (so if
    # the user supplied "trade_name, sum(backages)" as input, this function will return with the third element 
    # being a list containing ["trade_name", "backwages"]).

    user_columns = []
    sql_string_group = ""


    if user_columns_string == "":
        # No column list supplied so using the defaults
        sql_string_select = columns_default
        
    else:
        # User suplied value for the columns argument
        
        if user_columns_string.strip().lower() == "all":
            # User wants all columns
            sql_string_select = columns_all
            
        elif user_columns_string.strip().lower() == "default":
             # User is specifying defaults wanted
             sql_string_select = columns_default
             
        else:
            # User is supplying a custom list of columns. Need to:
            # 1) Prevent SQL injection attacks by verifying the contents requested. This is done by parsing the request and making sure
            #    that each comma separated value is a valid column name or an aggregate function applied to a valide column name.
            # 2) For each aggregate function add an AS to the select so that ORDER BY will work on that column.
            # 3) Automatically build the GROUP BY part of the query for requests that have aggregate functions. This means that the user
            #    can just supply a columns parameter of "state,sum(backwages)" and the "state" column will automatically be added
            #    to the GROUP BY statement. If this isn't done, the code will generate a SQL error when run.
            sql_string_select = user_columns_string
             
             
            # Make a list out of the user supplied columns and remove white space
            user_columns_list = [x.strip() for x in user_columns_string.split(',')]
            
            
            no_aggregate_functions_used = True
            # loop through each requested column
            for user_column in user_columns_list:
                
                # check to see if there is an aggregate function. If so, strip it out to get just the column name.
                user_column_final = user_column
                if user_column[-1] == ")":
                    
                    # If there's a ")" at the end, then the only thing that would work is an aggregate function so we assume it is
                    # and strip out what would be the column name, i.e. remove the first 4 characters and the last. That means
                    # "Sum(backwages) would become just "backwages"
                    user_column_final = user_column[4:-1]
                    aggregate_function = user_column[0:3]

                    # Found an aggregate function so setting this to false for later use
                    no_aggregate_functions_used  = False


                    # This line adds an AS statement to aggregate functions. Example:
                    # "SELECT Sum(backwages) FROM cases ORDER BY backwages" is changed to
                    # "SELECT Sum(round(cast(backwages as numeric),2)) AS backwages FROM cases ORDER BY backwages"
                    # This is needed or Postrgres will fail due to "backwages" not being defined as a column and
                    # the rounding and cast functions are needed so that Postgres returns just two digits

                    #sql_string_select = sql_string_select.replace(
                    #    user_column, 
                    #    " " + aggregate_function + "(cast(" + user_column_final + "::numeric as money)) AS " + user_column_final
                    #)
                    
                    sql_string_select = sql_string_select.replace(user_column, user_column + " AS " + user_column_final)
                elif user_column.lower() =="cases_count":
                    # The user wants to know how many cases there are for each record returned. This is really
                    # only useful when the user also provides an aggregate function like sum for another field.

                    sql_string_select = sql_string_select.replace(user_column, "count(case_id) as cases_count")
                    user_column_final = "cases_count"

                else:
                    # OK, this is a normal column, not an aggregate function, so add it as a column to group by
                    # in case there is at least one other column that does use an aggregate function.
                    if sql_string_group == "":
                        # add the "GROUP BY" text if this is the first column
                        sql_string_group = "GROUP BY "
                    else:
                        # add a comma if this is not the first column
                        sql_string_group += ","
                    sql_string_group += user_column_final

                # raise an error if the column requested does not exist and is not the special cases_count column
                # which returns the number of records
                if user_column_final not in columns_all_list and user_column_final !="cases_count":    
                    abort(409, description="The requested column '" + user_column_final +"' does not exist")
                
                user_columns.append(user_column_final)
            
            # ok, verified that all the requested columns are valid columns
            
        
            # Build the order by SQL string
            if no_aggregate_functions_used:
                # There were no aggregate functions used so no grouping needed.
                sql_string_group = ""

    return (sql_string_select, sql_string_group, user_columns) 


import datetime
def create_sql_where_string(user_columns = {}, user_where = "", user_company_name = "", user_dates = "", user_industry = ""):

    sql_string_where = ""
    sql_params = []

    # THIS IS NOT SAFE YET - VULNERABLE TO SQL INJECTIONS
    if user_where  != "":
        sql_string_where = " where " + user_where


    for user_column_key in user_columns:

        if user_columns[user_column_key] != "":

            sql_string_where += where_or_and_as_needed(sql_string_where)


            if user_column_key in ["city", "county"]:

                sql_string_where += " LOWER(" + user_column_key + ") = %s "
                sql_params.append(user_columns[user_column_key].strip().lower())

            else:

                sql_string_where += " " + user_column_key + " = %s "
                sql_params.append(user_columns[user_column_key].strip().upper())

    if user_industry != "":

        sql_string_where += where_or_and_as_needed(sql_string_where)

        sql_string_where += " tsv_industry @@ plainto_tsquery(%s)" 
        sql_params.append(user_industry)
    

    if user_company_name != "":

        sql_string_where += where_or_and_as_needed(sql_string_where)

        sql_string_where += " tsv @@ plainto_tsquery(%s)" 
        sql_params.append(user_company_name)
    
    if user_dates !="":
        sql_string_where += where_or_and_as_needed(sql_string_where)

        dates_list  = [x.strip() for x in user_dates.split(',')]

    
        if len(dates_list) == 1:

            try:
                datetime.datetime.strptime(dates_list[0], '%Y-%m-%d')
            except ValueError:

                if len(dates_list[0]) == 4:
                    sql_string_where += " findings_end_date BETWEEN %s AND %s "
                    sql_params.append(dates_list[0] + "-01-01") 
                    sql_params.append(dates_list[0] + "-12-31")
                else:
                    abort(409,description="The string '" + dates_list[0] + "' is not a valid date or year.")
            else:
                sql_string_where += " findings_end_date = %s "
                sql_params.append(dates_list[0]) 

        elif len(dates_list) == 2:

            count = 0
            for a_date in dates_list:

                try:
                    datetime.datetime.strptime(a_date, '%Y-%m-%d')
                except ValueError:
                    if len(a_date) == 4:
                        if count==0:
                            dates_list[count] = a_date + "-01-01"
                        if count==1:
                            dates_list[count] = a_date + "-12-31"
                    else:
                        abort(409,description="The string '" + a_date + "' is not a valid date or year.")

                count += 1


            sql_string_where += " findings_end_date BETWEEN %s AND %s "
            sql_params.append(dates_list[0]) 
            sql_params.append(dates_list[1])

        else:
            abort(409, description="Only two comma separated dates can be entered as an input for the dates option.")

    return (sql_string_where, sql_params)



def where_or_and_as_needed(sql_string_where):

    if len(sql_string_where) == 0:
        return " WHERE "
    else:
        return " AND "


# This is a general function that takes as its input a SQL query string and returns
# a data structure containing the results of that query.
def get_data(sql_query = "",select = "", user_columns = [], from_table = "", where = "", group = "", limit_and_offset = "", order = "", sql_params=[], return_format = "default"):
    
    conn = e.connect()
    
    records_filtered = 0
    records_total = 0
    
    if return_format == "default":
        # Get count of records in table after filter (where statement) is applied
        records_filtered = conn.execute("SELECT Count(*) FROM " + from_table + " " + where, sql_params).cursor.fetchone()[0]
       
    
        # Get total count of records in table without filter
        records_total= conn.execute("SELECT Count(*) FROM " + from_table + " ", sql_params).cursor.fetchone()[0]


    # The user may pass in a fully formed SQL query. If not, we build it here from the pieces.
    if sql_query == "":
        sql_query = "SELECT " + select + " FROM " +from_table + " " + where + " " + group + " " + order + " " + limit_and_offset 
        print("SQL QUERY:" + sql_query)
        
    query = conn.execute(sql_query, sql_params)
    rows = query.cursor.fetchall()
    
    if return_format in("default", "html", ""):
        keys = [member[0] for member in query.cursor.description]
    
        results = []
    
        for row in rows:
            result_dict = {}
            
            # THIS MAY NOT WORK WITH SUMS MAX MIN ETC. DUE TO MEMBER[0] RETURNING THE AGGREGATE FUNCTION INSTEAD OF THE COLUMN_NAME
            
            for key, value in zip(keys, row): # column_name, column_value
                result_dict[key] = value
            results.append(result_dict)
    
        return {'data': results, 'recordsTotal': records_total, 'recordsFiltered': records_filtered  }
    elif return_format =="googledatatable":
            
        keys =[]
        temp_count = 0
        for member in query.cursor.description:
            if int(member[1]) == 25:
                string_type = "string"
            else:
                string_type = "number"
            
            # If there is an aggregate function, query.cursor.description returns that function's name instead of the column name.
            # So if in the query string the user wanted sum(backwages), query.cursor.description[0] will return "sum" instead of "backwages'
            # This means if it's a user supplied sql select, then we need to use a list of columns supplied to this function instead of
            # getting the descriptions from query.cursor.description.
            if not user_columns:
                temp_column_label = column_labels[member[0]]
            else:
                temp_column_label = column_labels[user_columns[temp_count]] # 
            
            keys.append({"label": temp_column_label, "type": string_type})
            
            temp_count += 1
            
        columns = []
        for key in keys:
            columns.append({"label": key['label'], "type": key['type']})
        
        rows_return = []
        for row in rows:
            row_return = []
            
            for key, value in zip(keys, row): # column_name, column_value
                row_return.append({"v": value})
                
            rows_return.append({"c": row_return})            
                
        return {"cols": columns, "rows":rows_return}
    else:
        abort(409,description="Valid values for the return_format parameter are csv, GoogleDataTable, HTML, or Default. The type '" + return_format + "'is not valid.")





# This is a general function that takes as its input a SQL query string and
# a list of the column headers and returns a string that contains the contents of
# a CSV file.
def get_data_csv(sql_query, sql_params=[]):

        conn = e.connect()

        query = conn.execute(sql_query, sql_params)
        rows = query.cursor.fetchall()
        keys = [member[0] for member in query.cursor.description]


        import csv
        dest = StringIO()
        writer = csv.writer(dest)

        writer.writerow(keys)
        
        writer.writerows(rows)
        return_string = dest.getvalue()
        dest.close()
        
        return return_string
   

# If request.args not set, then this function returns "". Otherwise, returns the value in request.args. 
# This function is handy because otherwise every time you want to see if there is a value in request.args
# you first have to check to see if it exists at all.
def safe_arg(request_arg):


    if request_arg not in request.args:
        return ""
    else:
        return request.args[request_arg]



# Add all REST definitions here
api.add_resource(Case, '/api/v1/cases/<case_id>')
api.add_resource(CaseList, '/api/v1/cases')

if __name__ == '__main__':
    app.run()
