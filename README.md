## Daily Data Check Push Notifier
 I am working on a project where I need to enter self-assessment data on a daily basis, but it can be easy to forget days. This script checks the source google sheet and sends me a push notification if any issues are detected, including missing days, duplicates or script execution errors. This helps me build a high-quality dataset.
 
 The script runs once per day, hosted on pythonanywhere.com.
 
 ### Features / Notice Types
 
 #### Missing Data Notice
 
 Only sends the push notification if the data is missing any dates from the range of dates elapsed since the start of the project.
 
 <img src="https://user-images.githubusercontent.com/107285758/173174923-12d066f9-8bdb-4736-84e5-8fabcc590814.jpg" width="250">
  
 #### Duplicate Data Notice
 
 If a line of data was entered twice for the same day, this notice is sent.
 
 <img src="https://user-images.githubusercontent.com/107285758/173174314-1b4ed478-4599-4bb8-af00-a184c31d16c8.jpg" width="300">
  
 #### Script Error Notice
 
 If the script errors out for whatever reason, I am sent a push notification with the error description.
 
 <img src="https://user-images.githubusercontent.com/107285758/173174316-1f8e72a6-d08f-4c22-b1ed-27f5c3157991.jpg" width="250">
