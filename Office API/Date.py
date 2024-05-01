from datetime import datetime, timedelta

class DefaultDates():
    '''if end_date = None, take today - exlcude
    if start_date = None, table end_date - period + 1'''
    
    def __init__(self, start_date = None, end_date = None, period = 30, exclude = 1, dateform_input = '%Y-%m-%d'):
        
        if end_date:
            self.END_DATE = datetime.strptime(end_date, dateform_input)
        elif not start_date:
            self.END_DATE = datetime.today() - timedelta(days = exclude)
            
        if start_date:
            self.START_DATE = datetime.strptime(start_date, dateform_input)
            if not end_date:
                self.END_DATE = self.START_DATE + timedelta(days = period - 1)
        else:
            self.START_DATE = self.END_DATE - timedelta(days = period - 1)
        
    def InDates(self):
        '''return in datetime format'''
        # print(self.START_DATE, 'to', self.END_DATE)
        return self.START_DATE, self.END_DATE
    
    def InSTRs(self, dateform_output = '%Y-%m-%d'):
        '''return in a certain string format'''
        # print(self.START_DATE.strftime('%Y-%m-%d'), 'to', self.END_DATE.strftime('%Y-%m-%d'))
        return self.START_DATE.strftime(dateform_output), self.END_DATE.strftime(dateform_output)
    
    def DayDiff(self, form = 'days'):
        diff = (self.END_DATE - self.START_DATE)
        if form == 'days':
            return diff.days
        elif form == 'months':
            return diff.months
        elif form == 'years':
            return diff.years
        
        
    def Intervals_InDates(self, interval = 1):
        date_list = []
        S = self.START_DATE
        E = S + timedelta(days = interval-1)
        date_list.append([S, E])
        
        if self.DayDiff() + 1 > interval:
            while E < self.END_DATE:  
                S = E + timedelta(days = 1)
                E = min(S + timedelta(days = interval-1), self.END_DATE)
                date_list.append([S, E])

            
        return date_list
    
    
    def Intervals_InSTRs(self, interval = 1, dateform_output = '%Y-%m-%d'):
        
        date_list_raw = self.Intervals_InDates(interval)
        date_list = []
        
        for pair in date_list_raw:
            date_list.append([
                pair[0].strftime(dateform_output), 
                pair[1].strftime(dateform_output)])
        return date_list
            