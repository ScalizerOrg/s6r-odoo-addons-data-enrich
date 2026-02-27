# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _
from odoo.fields import Domain


class CrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', 'insee.partner.mixin']

    siret = fields.Char(string='SIRET')
    web_category = fields.Char()
    linkedin_url = fields.Char()
    capital = fields.Float()
    turnover = fields.Float()
    owners = fields.Text()
    company_object = fields.Text()

    def _prepare_enriched_values(self, values=None):
        values = super(CrmLead, self)._prepare_enriched_values(values)
        if values.get('country_id') and isinstance(values.get('country_id'), dict):
            country_val = values['country_id']
            domain = []
            if country_val.get('name'):
                domain.append([('name', '=', country_val['name'])])
            if country_val.get('code'):
                domain.append([('code', 'ilike', f"{country_val['code']}%" )])
            if len(domain) > 1:
                domain = Domain.OR(domain)
            country_id = self.env['res.country'].search(domain)
            if country_id:
                values['country_id'] = country_id
            else:
                values.pop('country_id')
        if values.get('name') and not values.get('partner_name'):
            values['partner_name'] = values.get('name')
        if values.get('description', False) and self.description:
            self.description += '\n %s' % values.pop('description')
        if values.get('objet', False):
            values['company_object'] = values.pop('objet')
        return values

    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        res = super(CrmLead, self)._prepare_customer_values(partner_name, is_company=is_company, parent_id=parent_id)
        m_partner = self.env['res.partner']
        insee_mixin = self.env['insee.partner.mixin']
        mixin_fields = insee_mixin._fields.keys()
        res['siret'] = self.siret
        def _check_field(field):
            return hasattr(m_partner, field) and hasattr(self, field) and self[field] and field not in res
        lead_values = {k: self[k] for k in mixin_fields if _check_field(k)}
        res.update(lead_values)
        return res
