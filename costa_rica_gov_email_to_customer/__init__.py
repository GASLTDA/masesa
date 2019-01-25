from . import models
from odoo import api, SUPERUSER_ID

def _auto_install_data(cr, registry):

    env = api.Environment(cr, SUPERUSER_ID, {})
    invoice_ids = env['account.invoice'].search([('haicenda_status', '=', 'aceptado'),('type','in',['out_invoice', 'out_refund'])])
    print(invoice_ids)
    for invoice_id in invoice_ids:
        invoice_id.write({'email_sent':True})
