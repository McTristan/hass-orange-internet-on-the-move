class ConsumptionOfDevice:
    def __init__(self, contract_type, initial_data, left_data, expiry_date, start_date):
        self.type = contract_type
        self.initial_data = initial_data
        self.left_data = left_data
        self.expiry_date = expiry_date
        self.start_date = start_date

    def __repr__(self):
        return str(self.__dict__)


# for later use
class SubscriptionOfDevice:
    def __init__(self, todo):
        self.todo = todo

    def __repr__(self):
        return str(self.__dict__)


class Device:
    def __init__(self, device_id, country, status, tag, user_id, user_name, creation_date, serial_number):
        self.device_id = device_id
        self.country = country
        self.status = status
        self.tag = tag
        self.user_id = user_id
        self.user_name = user_name
        self.creation_date = creation_date
        self.serial_number = serial_number

    def __repr__(self):
        return str(self.__dict__)


class OBSFullData:
    def __init__(self, device: Device, consumption: ConsumptionOfDevice):
        self.device = device
        self.consumption = consumption

    def __repr__(self):
        return str(self.__dict__)
