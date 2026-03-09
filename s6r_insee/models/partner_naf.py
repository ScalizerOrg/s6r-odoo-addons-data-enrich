# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models, _
from odoo.fields import Domain
try:
    from s6r_sirene.metadata import get_activity_list# pylint: disable=missing-manifest-dependency
except:
    pass
    def get_activity_list():
        return []
import logging

_logger = logging.getLogger(__name__)


class PartnerNaf(models.Model):
    _name = 'partner.naf'
    _description = 'NAF APE'

    name = fields.Char()
    naf_code = fields.Char('NAF Code', index=True)
    display_name = fields.Char(compute='_compute_display_name',  search='_search_display_name')

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[%s] %s' % (rec.naf_code, rec.name)

    @api.model
    def _search_display_name(self, operator, value):
        if operator not in ('=', 'ilike') or not isinstance(value, str):
            return super(PartnerNaf, self)._search_display_name(operator, value)

        return Domain.OR([
            [('name', operator, value)],
            [('naf_code', operator, value)]
        ])

    @api.model
    def import_naf_list(self):
        df_activities = get_activity_list('NAF5')
        naf_codes = list(df_activities.get(['NAF5','TITLE_NAF5_FR']).itertuples())
        for naf in naf_codes:
            if self.search_count([('naf_code', '=', naf.NAF5)]):
                continue
            self.create({'name': naf.TITLE_NAF5_FR, 'naf_code': naf.NAF5})

        return {
            'name': _('NAF APE Codes'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'target': 'current',
            'res_model': self._name,
        }
