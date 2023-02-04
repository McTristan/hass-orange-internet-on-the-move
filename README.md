# Orange "Internet On the move" Renault Home Assistant Integration

https://internetonthemove.orange-business.com/
This integration retrieve data consumption of your Renault car.

### Datas

You'll get :
* Start date of your plan
* End date of your plan
* Initial data amount of the plan
* Data Left
* Percentage of data left
* Plan type
* Serial number of your car

### Installation

Copy this folder to `<config_dir>/custom_components/orange_internet_on_the_move/`.

Then rendez-vous in the Integration menu of Home Assistant and search for "Orange Internet on the move" and follow the configuration assistant.

### Information

The integration will refresh data from internet every hour.

### Limitation

Retrieve the `onetime` plan for only one car at the moment.