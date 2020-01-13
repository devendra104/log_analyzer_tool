# log_analyzer_tool

Log Analyzer tool analyze and keep the build to build data in some specific manner  which
helps to catch the error, warning, alert, commands execution status, pattern to pattern
suspicious message and publishing it on the dashboard.  

The record stores in database will be available fore-ever until someone do not delete it, but the xls report contains the data of requested build only.

In simple term we are providing the platform where everyone will keep there build related alerts, warning or some specific highlighted information in database for future analysis.
 
We have designed the dashboard of log analyzer tool in flask that had multiple options
like below

![picture](/home/desingh/Pictures/Log_Analzer_Dashboard.png)

The first option is "Trigger Log Analysis", If you click on this option then you get the next page, where we ask to user please provide the below information.

![picture](/home/desingh/Pictures/job_analysis_input_menu.png)

1: First one is "job name", Job Name selection happens on the basis of sub_job.yaml file which creates at the run time according to the requested version.

2: Second one is "Validator", Validator depends on the analysis type, like what kind of analysis you want to perform, 

3: Third one is "Job Number", If you do not pass the build number then it automatically select the recent build. 

4: Forth one is "Component version", It use to create the sub_job.yaml and validation.yaml version wise. 

5: Fifth one is "Check on Build machine" If you want to do the analysis on the build machine the select the check on build machine otherwise we can select the no check on build machine.


Once you pass the require information then click on the submit button then the log analysis trigger in the background we wait for their progress completion
once it has completed we comes to the "Job analysis main menu"

![picture](/home/desingh/Pictures/Analysis.png)

The Second option of Main menu is build history, yet now it contains the two type of data, first related to customer DB and the second related to Satellite and Capsule upgrade.

![picture](/home/desingh/Pictures/build_history.png)

The third option of Main Menu is Build Job Search, //TODO

The forth option of Main Menu is Report Builder, Currently ths format we use mostly to build the report for customer db upgrade, In future we will enhance and publish some generalize solution.

![picture](/home/desingh/Pictures/report_builder.png)