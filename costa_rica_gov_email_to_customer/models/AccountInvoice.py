import base64
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    email_sent = fields.Boolean(default=False)

    @api.multi
    def auto_email(self):
        ids = self.env['account.invoice'].search([('haicenda_status', '=', 'aceptado'),('type','in',['out_invoice', 'out_refund']),('email_sent', '=', False)])

        for id in ids:
            try:
                template = self.env.ref('account.email_template_edi_invoice', False)

                if template.id:

                    mail_id = template.send_mail(id.partner_id.id)
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

            except:
                pass

        return True

    @api.multi
    def _send_mail_to_attendees(self, template_xmlid, force_send=False):
        res = False

        if self.env['ir.config_parameter'].sudo().get_param('calendar.block_mail') or self._context.get(
                "no_mail_to_attendees"):
            return res

        calendar_view = self.env.ref('calendar.view_calendar_event_calendar')
        invitation_template = self.env.ref(template_xmlid)

        # get ics file for all meetings
        ics_files = self.mapped('event_id').get_ics_file()

        # prepare rendering context for mail template
        colors = {
            'needsAction': 'grey',
            'accepted': 'green',
            'tentative': '#FFFF00',
            'declined': 'red'
        }
        rendering_context = dict(self._context)
        rendering_context.update({
            'color': colors,
            'action_id': self.env['ir.actions.act_window'].search([('view_id', '=', calendar_view.id)], limit=1).id,
            'dbname': self._cr.dbname,
            'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url',
                                                                         default='http://localhost:8069')
        })
        invitation_template = invitation_template.with_context(rendering_context)

        # send email with attachments
        mails_to_send = self.env['mail.mail']
        for attendee in self:
            if attendee.email or attendee.partner_id.email:
                # FIXME: is ics_file text or bytes?
                ics_file = ics_files.get(attendee.event_id.id)
                mail_id = invitation_template.send_mail(attendee.id)

                vals = {}
                if ics_file:
                    vals['attachment_ids'] = [(0, 0, {'name': 'invitation.ics',
                                                      'mimetype': 'text/calendar',
                                                      'datas_fname': 'invitation.ics',
                                                      'datas': base64.b64encode(ics_file)})]
                vals['model'] = None  # We don't want to have the mail in the tchatter while in queue!
                vals['res_id'] = False
                current_mail = self.env['mail.mail'].browse(mail_id)
                current_mail.mail_message_id.write(vals)
                mails_to_send |= current_mail

        if force_send and mails_to_send:
            res = mails_to_send.send()
