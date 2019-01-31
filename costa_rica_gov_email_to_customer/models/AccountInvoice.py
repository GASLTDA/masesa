import base64
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    email_sent = fields.Boolean(default=False)

    @api.multi
    def auto_email(self):
        ids = self.env['account.invoice'].search([('haicenda_status', '=', 'aceptado'),('type','in',['out_invoice', 'out_refund']),('email_sent', '=', False)], order='id asc')

        for id in ids:
            try:
                template = self.env.ref('account.email_template_edi_invoice', False)

                if template.id:

                    mail_id = template.send_mail(id.id)
                    current_mail = self.env['mail.mail'].browse(mail_id)

                    if id.haicenda_status == 'aceptado':
                        try:
                            res = requests.post(id.company_id.url + '/api/download_xml', {
                                'key': id.company_id.access_token,
                                'clave': id.clave_numerica,
                                'vat': id.company_id.company_registry,
                                'date': str(id.date_invoice),
                            })

                            attachment_1 = self.env['ir.attachment'].sudo().create(
                                {'name': id.clave_numerica + '_submitted_file.xml',
                                 'mimetype': 'application/xml',
                                 'type': 'binary',
                                 'datas_fname': id.clave_numerica + '_submitted_file.xml',
                                 'datas': res.content,
                                 'res_model': 'account.invoice',
                                 'res_id': id.id,
                                 })
                            current_mail.attachment_ids = [(4, attachment_1.id)]
                        except requests.exceptions.RequestException:
                            raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                        except requests.exceptions.HTTPError:
                            raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                        except requests.exceptions.ConnectionError:
                            raise UserError(_('Algo salió mal, intente de nuevo más tarde'))
                        except requests.exceptions.Timeout:
                            raise UserError(_('Algo salió mal, intente de nuevo más tarde'))

                    if id.response_xml != False or id.response_xml != None:
                        attachment_2 = self.env['ir.attachment'].sudo().create(
                        {'name': id.clave_numerica + '_response_file.xml',
                         'mimetype': 'application/xml',
                         'type': 'binary',
                         'datas_fname': id.clave_numerica + '_response_file.xml',
                         'datas': base64.b64encode(str(id.response_xml).encode()),
                         'res_model': 'account.invoice',
                         'res_id': id.id,
                         })

                        current_mail.attachment_ids = [(4, attachment_2.id)]

                    current_mail.send()
                    id.email_sent = True

            except:
                pass

        return True
