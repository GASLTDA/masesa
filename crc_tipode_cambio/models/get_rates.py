import datetime

from odoo import models, api, fields

class GetRates(models.TransientModel):
    _name = 'get.rates'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    @api.multi
    def get_rate(self):
        for dt in self.daterange(datetime.datetime.strptime(self.date_from,"%Y-%m-%d").date(), datetime.datetime.strptime(self.date_to,"%Y-%m-%d").date()):
            self.env['crc_currency_rate'].sudo()._update_crc_manual(dt)

    def daterange(self, date1, date2):
        for n in range(int ((date2 - date1).days)+1):
            yield date1 + datetime.timedelta(n)
