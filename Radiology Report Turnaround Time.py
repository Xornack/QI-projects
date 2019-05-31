# -*- coding: utf-8 -*-
"""
Created on Mon Oct 22 20:46:26 2018
Basic descriptive statistics and difference testing for US QI project.
We changed the ultrasound template to allow the technologists to input data
into the template. Our job becomes looking at the images and clicking through 
the exam if we agree.

Is there a difference in the 6 months before implementation and the 6 months
after? We gave 6 months for a learning curve.

Measure: time from exam completed to when the resident signs the report and 
time from exam completed to when attending signs the report. The time it
actually takes to make a report is not easily available. Ultimately I searched
in Nuance mPower (Montage) for the appropriate date ranges. I changed the date
fields in excel to the "YYYY-MM-DDTHH:MM" format required by ISO-8601. Numpy's
datetime64 function will ultimately rely on it, and it makes subsetting in SQL
easier.

Example SQLite queries:

SELECT "Exam Completed Date", "Exam Completed to Preliminary Report (minutes)", "Exam Completed to Report Finalized (minutes)"
FROM US_QI
WHERE "Patient Status" = "Emergency";

SELECT "Exam Completed Date", "Exam Completed to Preliminary Report (minutes)", "Exam Completed to Report Finalized (minutes)"
FROM US_QI
WHERE time("Exam Completed Date") BETWEEN time("12:00") AND time("13:00")
AND cast(strftime('%w', "Exam Completed Date") as integer) BETWEEN 1 AND 5;    

The results: no measurable difference before and after intervention. I think
the main difficulty is in actual time to create a report, which we aren't
directly capturing. There's a myriad of factors that affect time to open a report
and start editing it, so that was one major limitation. There are some simple
but very useful functions here though.

Other result: I found no difference between tech time before and 
after intervention, which was valuable information to us.

Another idea: these are time series data and fit a Poisson distribution, but
there's not a built in difference test for Poisson distributions that I could
find (E-score), so I'd have to build one. Project for another time...
@author: gamem
"""
import csv
import numpy as np
import matplotlib.pyplot as plt # use this in the console to check out the data
#from scipy.stats import ttest_ind

# Read in csv. Saved a .csv in Excel from the SQLite query.
def read_in_csv(path):
    data = []
    with open(path) as csvfile:
        csv_file = csv.reader(csvfile, dialect='excel')
        for row in csv_file:
            data.append(row)
    return np.array(data)

# Read in and get the columns we want. The variable names say it all.
# Note: the dtype has to be in an int or a float to do math, default is string
# when you read in the way I did.
data = read_in_csv('E:/SQL_DATABASES/Lunch_Coverage_US.csv')
data = np.matrix.transpose(data)
exam_completed_dates = [np.datetime64(i) for i in data[0][1:]]
time_to_prelim = data[1][1:].astype(dtype = np.int16)
time_to_finalize = data[2][1:].astype(dtype = np.int16)

#plt.hist(time_to_prelim, bins = 100)
#plt.hist(time_to_finalize, bins = 100)

'''
Just of interest:
Example of how to convert np.timedelta64 to floats:
x = exam_completed_dates[1] - exam_completed_dates[0]
x.astype('timedelta64[m]') / np.timedelta64(1, 'm')
https://docs.scipy.org/doc/numpy-1.13.0/reference/arrays.datetime.html
'''
# Return an array that subsets the array by time.
# The time has to be in the np.datetime64 format e.g. '2017-11-01T00:00'.
def subset_by_time(datetime_array,
                   subset_array,
                   lower = False, 
                   higher = False):
    if lower == False and higher == False:
        print("There aren't any ranges given.")
    
    if higher != False:
        indices = np.where(datetime_array < np.datetime64(higher))[0]
        
    if lower != False:
        indices = np.where(datetime_array > np.datetime64(lower))[0]
        
    if lower != False and higher != False:
        indices1 = np.where(datetime_array < np.datetime64(higher))[0]
        indices2 = np.where(datetime_array > np.datetime64(lower))[0]
        indices = np.array(list(set(indices1).intersection(indices2)))
        
    return np.array([subset_array[i] for i in indices])
    

# Find the median and IQR of an array.
def med_IQR(l):
    if type(l) == list:
        l = np.array(l)
    median = np.median(l)
    q1, q3 = np.percentile(l, [25, 75])
    IQR = q3 - q1
    return [median, q1, q3, IQR]

# Find the mean and standard deviation of a list. Just useful if I want it.
# These data are heavily skewed, so mean is a bad measure of middle.
def mean_std(l):
    if type(l) == list:
        l = np.array(l)
    mean = np.mean(l)
    std_dev = np.std(l)    
    return [mean, std_dev]

# Time values of interest. The intervention was started in 10/2017.
# I only got patients from 6 months before that through 10/1/2018.
time1 = '2017-10-01T00:00'
time2 = '2018-04-01T00:00'

# Get the first six months resident read and attending read.
# "First six months time to prelim/final read"
# the 'f' and 'l' at the start of the variable names
# 'f' means 'first' a la 'first six months'.
# and 'l' means 'last' a la "last six months'.
f_tt_prelim_read = subset_by_time(exam_completed_dates,
                                    time_to_prelim,
                                    lower = False,
                                    higher = time1)

f_tt_final_read = subset_by_time(exam_completed_dates,
                                   time_to_finalize,
                                   lower = False,
                                   higher = time1)

l_tt_prelim_read = subset_by_time(exam_completed_dates,
                                    time_to_prelim,
                                    lower = time2,
                                    higher = False)

l_tt_final_read = subset_by_time(exam_completed_dates,
                                   time_to_finalize,
                                   lower = time2,
                                   higher = False)

f_prelim_stats = med_IQR(f_tt_prelim_read)
f_final_stats = med_IQR(f_tt_final_read)
l_prelim_stats = med_IQR(l_tt_prelim_read)
l_final_stats = med_IQR(l_tt_final_read)

# Show median stats.
print("Resident read stats:")
print("Baseline ", f_prelim_stats)
print("Last 6 months ", l_prelim_stats)
print("")
print("Final read stats:")
print("Baseline ", f_final_stats)
print("Last 6 months ", l_final_stats)
print('')

#ttest_ind(f_tt_prelim_read, l_tt_prelim_read)
#ttest_ind(f_tt_final_read, l_tt_final_read)










