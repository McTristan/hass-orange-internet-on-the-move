class ConsumptionOfDevice:
    def __init__(self, contract_type, initial_data, left_data, expiry_date, start_date):
        self.type = contract_type
        self.initial_data = initial_data
        self.left_data = left_data
        self.expiry_date = expiry_date
        self.start_date = start_date

    def __repr__(self):
        return str(self.__dict__)
