# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SearchSireneResult(models.TransientModel):
    _name = 'search.sirene.result'
    _description = 'Search Sirene Result'
    _inherit = ['insee.enriched.fields.mixin', 'insee.partner.mixin']

    wizard_id = fields.Many2one('search.sirene.wizard')
    model = fields.Char()
    target_model = fields.Char(compute='_compute_target_model')
    values = fields.Json()
    opendata_json_values = fields.Json(copy=False)

    def _compute_target_model(self):
        for rec in self:
            rec.target_model = rec.wizard_id.model or rec.model

    def _prepare_enriched_result_values(self):
        vals = {
            'name': self.name,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'country_id': self.country_id.id,
        }
        m_model = self.env[self.wizard_id.model or self.model]
        if hasattr(m_model, 'partner_name'):
            vals['partner_name'] = self.name
        if hasattr(m_model, 'siren'):
            vals['siren'] = self.siren
        if hasattr(m_model, 'nic'):
            vals['nic'] = self.nic
        if hasattr(m_model, 'siret'):
            vals['siret'] = self.siret
        if self.ape_code and hasattr(m_model, 'naf_id'):
            naf_id = self.env['partner.naf'].search([('naf_code', '=', self.ape_code)], limit=1)
            if naf_id:
                vals['naf_id'] = naf_id.id

        enriched_fields_mixin = self.env['insee.enriched.fields.mixin']
        enriched_fields = enriched_fields_mixin._fields.keys()
        def _check_field(field):
            return hasattr(m_model, field) and hasattr(self, field) and self[field] and field not in vals
        def _field_value(field):
            return self[field].id if isinstance(self[field], models.BaseModel) else self[field]
        other_values = {k: _field_value(k) for k in enriched_fields if _check_field(k)}
        vals.update(other_values)
        return vals

    def action_update_record(self):
        if not self.wizard_id.model:
            raise UserError(_("No target model"))
        vals = self._prepare_enriched_result_values()
        m_model = self.env[self.wizard_id.model]
        if self.wizard_id.partner_id:
            self.wizard_id.partner_id.write(vals)
        else:
            if hasattr(m_model, 'siret'):
                record_id = m_model.search([('siret', '=', self.siret)], limit=1)
            else:
                record_id = m_model.search([('name', 'ilike', self.name)], limit=1)
            if record_id and self.wizard_id.model == 'res.partner':
                msg = _('A similar record already exists. %s, id=%s') # pylint: disable=translation-positional-used
                raise UserError(msg % (record_id.name, record_id.id))
            if hasattr(m_model, 'company_type'):
                vals['company_type'] = 'company'
            record_id = m_model.create(vals)
            action = {
                'view_mode': 'form',
                'res_model': self.wizard_id.model,
                'res_id': record_id.id,
                'type': 'ir.actions.act_window',
                'target': 'main',
            }
            return action
