# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class InpiAttachment(models.TransientModel):
    _name = 'inpi.attachment'
    _description = 'INPI Attachment'

    name = fields.Char()
    key = fields.Char()
    type = fields.Selection(selection=[('actes', 'Deed'), ('bilans', 'Balance'), ('bilans-saisis', 'Entry Balance')])
    attachment_date = fields.Date()
    data = fields.Binary('File')

    def download_inpi_attachment(self):
        res = self.env['inpi.partner.mixin'].download_inpi_attachment(self.type, self.key)
        self.data = base64.b64encode(res)
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/inpi.attachment/%s/data/%s.pdf?download=true' % (self.id, self.key),
            'target': 'new',
        }
