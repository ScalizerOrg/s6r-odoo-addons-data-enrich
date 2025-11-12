# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from s6r_sirene.sirene import get_sirene_data # pylint: disable=missing-manifest-dependency
from s6r_sirene.sirene import _street_metadata as street_metadata # pylint: disable=missing-manifest-dependency
from s6r_sirene.metadata import get_legal_entity # pylint: disable=missing-manifest-dependency
from s6r_sirene.utils import init_conn # pylint: disable=missing-manifest-dependency
import datetime
import logging

_logger = logging.getLogger(__name__)


def numpy_val(val):
    if isinstance(val, float):
        return 0 if str(val) == 'nan' else float(val)
    if not hasattr(val, 'dtype'):
        return val
    if val.dtype == 'bool':
        return bool(val)
    if val.dtype == 'int64':
        return int(val)

    return str(val.values[0])

def insee_results_to_list(insee_result):
    if not hasattr(insee_result, 'values') and not insee_result:
        return []
    res = []
    for insee_value in insee_result.values:
        vals = {f: numpy_val(insee_value[i]) for i,f in enumerate(list(insee_result.columns))}
        res.append(vals)
    return res


class InseePartnerMixin(models.AbstractModel):
    _name = 'insee.partner.mixin'
    _description = 'Insee Partner Mixin'
    _inherit = ['inpi.partner.mixin', 'opendata.mixin']

    def _get_workforce_range_list(self):
        return [
            ('NN', _('Non-employing units')),
            ('00', _('0 employees')),
            ('01', _('1-2 employees')),
            ('02', _('3-5 employees')),
            ('03', _('6-9 employees')),
            ('11', _('10-19 employees')),
            ('12', _('20-49 employees')),
            ('21', _('50-99 employees')),
            ('22', _('100-199 employees')),
            ('31', _('200-249 employees')),
            ('32', _('250-499 employees')),
            ('41', _('500-999 employees')),
            ('42', _('1000-1999 employees')),
            ('51', _('2000-4999 employees')),
            ('52', _('5000-9999 employees')),
            ('53', _('10000+ employees')),
        ]

    siren = fields.Char('SIREN')
    workforce_range = fields.Selection(selection=_get_workforce_range_list)
    naf_id = fields.Many2one('partner.naf', string='NAF', index=True)
    naf_code = fields.Char(string='NAF Code', related='naf_id.naf_code')
    sirene_json_values = fields.Json(copy=False)
    establishment_creation_date = fields.Date()
    company_legal_type = fields.Char('Legal Type')
    company_category = fields.Char()
    administrative_state = fields.Char()
    legal_name = fields.Char()

    @api.model
    def init_sirene_connection(self):
        sirene_key = self.env['ir.config_parameter'].sudo().get_param('s6r_insee.sirene_key')
        if sirene_key:
            init_conn(sirene_key=sirene_key)

    def get_sirene_data(self, siret, retry=False):
        self.init_sirene_connection()
        try:
            return get_sirene_data(siret)
        except ValueError as err:
            if not retry:
                siren = self.siren if self.siren else siret[:9]
                return self.get_sirene_data(siren, retry=True)
            else:
                return {}
        except Exception as err:
            _logger.exception("Exception occurred : %s" % err, exc_info=True)

    def get_sirene_data_values(self):
        self.ensure_one()
        siret = hasattr(self, 'siret') and self.siret or ''
        siren = hasattr(self, 'siren') and self.siren or ''
        siren = siren.replace(' ', '')
        siret = siret.replace(' ', '')
        res = self.get_sirene_data(siret or siren)
        res_values = res[0] if res else {}
        values = {}
        if res_values:
            values = self.sirene_values_to_record_values(res_values)
        return values

    def action_get_sirene_data(self):
        for rec in self:
            values = self.get_sirene_data_values()
            rec.write(values)

    def sirene_values_to_record_values(self, res_values):
        values = {}
        street_types = {v[0]: v[1] for v in street_metadata._street_metadata().values if v[0].strip()}
        establishment = res_values.get('etablissement', {}) or res_values
        periods_etablissement = establishment.get('periodesEtablissement', [])
        period_etablissement = periods_etablissement[-1] if periods_etablissement else {}
        address = establishment.get('adresseEtablissement', {})
        unite_legale = establishment.get('uniteLegale', {})
        naf_code = unite_legale.get('activitePrincipaleUniteLegale', False) or period_etablissement.get(
            'activitePrincipaleEtablissement', False) or establishment.get(
            'activitePrincipaleRegistreMetiersEtablissement', False)
        if naf_code:
            naf_id = self.env['partner.naf'].search([('naf_code', '=', naf_code)], limit=1)
            if naf_id:
                values['naf_id'] = naf_id.id

        values['workforce_range'] = unite_legale.get('trancheEffectifsUniteLegale', False)

        street_name = address.get('libelleVoieEtablissement', '') or ''
        street_number = address.get('numeroVoieEtablissement', '') or ''
        street_type = address.get('typeVoieEtablissement', '') or ''
        street_type_name = street_types.get(street_type, street_type.capitalize() if street_type else '')

        street2 = address.get('complementAdresseEtablissement', '') or ''
        zip_code = address.get('codePostalEtablissement', '') or ''
        city = address.get('libelleCommuneEtablissement', '') or ''
        street = ' '.join(filter(None, [street_number, street_type_name, street_name]))
        if hasattr(self, 'street') and street:
            values['street'] = street
        if hasattr(self, 'street2') and street2:
            values['street2'] = street2
        if hasattr(self, 'zip') and zip_code:
            values['zip'] = zip_code
        if hasattr(self, 'city') and city:
            values['city'] = city
        if hasattr(self, 'siret') and not self.siret:
            values['siret'] = establishment.get('siret', '')
        if hasattr(self, 'siren') and not self.siren:
            values['siren'] = establishment.get('siren', '')
        if hasattr(self, 'legal_name'):
            values['legal_name'] = unite_legale.get('denominationUniteLegale', '')
        if hasattr(self, 'name') and not self.name:
            values['name'] = unite_legale.get('denominationUniteLegale', '')

        values['sirene_json_values'] = establishment if establishment else False

        values['establishment_creation_date'] = unite_legale.get('dateCreationUniteLegale', False)
        legal_entity_code = unite_legale.get('categorieJuridiqueUniteLegale', False)
        if legal_entity_code:
            legal_entity = get_legal_entity([legal_entity_code]).title.values[0]
            values['company_legal_type'] = legal_entity

        values['company_category'] = unite_legale.get('categorieEntreprise', False)
        country_code = address.get('codePaysEtrangerEtablissement', '') or 'FR'
        country_id = self.env['res.country'].search([('code', '=', country_code)], limit=1)
        values['country_id'] = country_id.id
        if values.get('dateCreationEtablissement'):
            creation_date = datetime.datetime.strptime(values.get('dateCreationEtablissement'), "%Y-%m-%d").date()
        elif unite_legale.get('dateCreationUniteLegale'):
            creation_date = datetime.datetime.strptime(unite_legale.get('dateCreationUniteLegale', False), "%Y-%m-%d").date()
        else:
            creation_date = False
        values['creation_date'] = creation_date

        return values

    def _prepare_enriched_values(self, values=None):
        self.ensure_one()
        try:
            if self.siren or hasattr(self, 'siret') and self.siret:
                res = self.get_sirene_data_values()
                values.update(res)
            else:
                res = self.search_sirene_database()
                values.update(res)

            siren = hasattr(self, 'siren') and self.siren or values.get('siren', '')
            siren = siren.replace(' ', '')
            if siren:
                res = self.get_inpi_company_data(siren)
                values.update(res)
                res = self.get_financial_ratios(siren)
                values.update(res)
        except Exception as err:
            _logger.exception("Exception occurred : %s" % err, exc_info=True)
            pass
        return values

    def _enrich_record(self, values=None):
        values = self._prepare_enriched_values(values)
        values.pop('id', None)
        values = {k: v for k, v in values.items() if hasattr(self, k) and values[k] and not self[k]}
        if values:
            self.write(values)
        return values

    def action_enrich_record(self, values=None, action=None):
        self.ensure_one()
        if values is None:
            values = {}
        if action is None:
            if self.env.context.get('soft_reload'):
                action = {
                    'type': 'ir.actions.client',
                    'tag': 'soft_reload',
                }
            else:
                action = {
                    'view_mode': 'form',
                    'res_model': self._name,
                    'res_id': self.id,
                    'type': 'ir.actions.act_window',
                    'target': 'main',
                }
            for rec in self:
                values = rec._enrich_record(values)
            return action

    def search_sirene_database(self, excluded_words=None):
        if excluded_words is None:
            excluded_words = ['SAS', 'SA', 'SARL', '', 'FRANCE', '&']

        keywords = []
        variable = []
        pattern = []

        if hasattr(self, 'name') and self.name:
            name = self.name.replace('.', '')
            if ',' in name:
                name = name.split(',')[0]
            name_words = name.split(' ')
            for name_word in name_words:
                if name_word.upper() not in excluded_words:
                    keywords.append(name_word)

            for keyword in keywords:
                variable.append('denominationUniteLegale')
                pattern.append(keyword)

            search_sirene_wizard = self.env['search.sirene.wizard'].create({'company_name': self.name})
            sirene_values = search_sirene_wizard.search_sirene(variable, pattern)
            if sirene_values:
                return self.sirene_values_to_record_values(sirene_values[0])
        return {}
