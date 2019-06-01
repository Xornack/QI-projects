# -*- coding: utf-8 -*-
"""
Created on Mon Oct 22 20:46:26 2018
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

Didn't end up needing SQL for these simpler queries.

@author: Matthew Harwood, MD
"""
import pandas
import numpy as np
import matplotlib.pyplot as plt # use this in the console to check out the data
from scipy.stats import ttest_ind

# Read in data.
data = pandas.read_csv('E:/SQL_DATABASES/US_limited_and_complete.csv')
exam_date = data['Exam Completed Date'].astype('datetime64[ns]')
turnaround_time = data['Exam Completed to Report Finalized (minutes)']

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

# Time values of interest.
time1 = '2017-10-01T00:00'
time2 = '2018-04-01T00:00'

# Find the time of the before and after interventions time.
turnaround_before = subset_by_time(exam_date,
                                   turnaround_time,
                                   lower = False,
                                   higher = time1)

turnaround_after = subset_by_time(exam_date,
                                  turnaround_time,
                                  lower = time2,
                                  higher = False)

medIQR_before = med_IQR(turnaround_before)
medIQR_after = med_IQR(turnaround_after)
print(medIQR_before)
print(medIQR_after)

fig, ax = plt.subplots()
ax.boxplot([turnaround_before, turnaround_after], 0, '')
ax.set_ylabel('Turnaround Time (minutes)')
ax.set_xticklabels(['Before Intervention', 'After Intervention'])
plt.show()

t, p = ttest_ind(turnaround_before, turnaround_after, equal_var = False)
