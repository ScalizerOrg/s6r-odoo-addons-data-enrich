# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models, _
from unidecode import unidecode
from s6r_sirene.sirene._request_sirene import _request_sirene as request_sirene # pylint: disable=missing-manifest-dependency
from s6r_sirene.sirene._clean_data import _clean_data as clean_data # pylint: disable=missing-manifest-dependency

import logging


_logger = logging.getLogger(__name__)

champs = [
    'siret',
    'siren',
    'nic',
    'dateCreationEtablissement',
    'denominationUniteLegale',
    'nomUniteLegale',
    'prenom1UniteLegale',
    'categorieJuridiqueUniteLegale',
    'activitePrincipaleUniteLegale',
    'nomenclatureActivitePrincipaleUniteLegale',
    'nicSiegeUniteLegale',
    'categorieEntreprise',
    'complementAdresseEtablissement',
    'numeroVoieEtablissement',
    'typeVoieEtablissement',
    'libelleVoieEtablissement',
    'codePostalEtablissement',
    'libelleCommuneEtablissement',
    'codeCommuneEtablissement',
]


def _search_sirene(query, kind, number):
    data_final = request_sirene(query=query, kind=kind, number=number)
    if not data_final:
        return []
    df = clean_data(data_final.copy(), kind=kind, clean=False)
    return df


class SearchSireneWizard(models.TransientModel):
    _name = 'search.sirene.wizard'
    _description = 'Search Partner in Sirene Database'

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        default_model = self.env.context.get('default_model', False)
        if default_model:
            defaults['model'] = default_model
        model = self.env.context.get('active_model', False) or default_model
        if self.env.context.get('active_id', False) and model:
            record_id = self.env[model].browse(self.env.context.get('active_id'))
            if hasattr(record_id, 'name') and record_id.name:
                defaults['company_name'] = record_id.name
            if hasattr(record_id, 'zip') and record_id.zip:
                defaults['zip_code'] = record_id.zip
            if hasattr(record_id, 'siren') and record_id.siren:
                defaults['siren'] = record_id.siren
            if hasattr(record_id, 'siret') and record_id.siret:
                defaults['siret'] = record_id.siret

        return defaults

    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    model = fields.Char(default='res.partner')
    result_ids = fields.One2many('search.sirene.result', 'wizard_id', string="Results")
    result_count = fields.Integer(readonly=True)
    company_name = fields.Char()
    zip_code = fields.Char()
    department = fields.Char('Department Code')
    naf_id = fields.Many2one('partner.naf', string='NAF Code')
    siren = fields.Char('SIREN', size=9)
    siret = fields.Char('SIRET', size=14)

    def _search_sirene(self, query, kind, number=100):
        try:
            results = _search_sirene(query, kind, number=number)
            return self.sort_results(results)
        except Exception as err:
            _logger.error(err, exc_info=True)
            pass
            return []

    def search_sirene(self, variable, pattern):
        self.env['insee.partner.mixin'].init_sirene_connection()
        try:
            param_list = list(zip(variable, pattern))
            name_params = [(v, p) for v, p in param_list if v == 'denominationUniteLegale']
            others_params = [(v, p) for v, p in param_list if v != 'denominationUniteLegale']
            name_condition = ' AND '.join(['%s:"%s"' % (variable, pattern) for variable, pattern in name_params])
            others_condition = ' AND '.join(['%s:%s' % (variable, pattern) for variable, pattern in others_params])
            query = '?q=%s' % ' AND '.join([c for c in [name_condition, others_condition] if c])
            results = self._search_sirene(query=query, kind='siret', number=100)
            if name_params:
                if not results:
                    query = '?q=(denominationUniteLegale:"%s")' % ' '.join([p for v, p in name_params])
                    query = query + others_condition if others_condition else query
                    results = self._search_sirene(query=query, kind='siret', number=100)
                if not results:
                    query = '?q=(denominationUniteLegale:"%s")' % ''.join([p for v, p in name_params])
                    query = query + others_condition if others_condition else query
                    results = self._search_sirene(query=query, kind='siret', number=100)
                if not results:
                    query = '?q=(denominationUniteLegale:"%s")' % unidecode(name_params[0][1])
                    query = query + others_condition if others_condition else query
                    results = self._search_sirene(query=query, kind='siret', number=100)

            return results
        except Exception as e:
            _logger.error(e, exc_info=True)
            return []

    def sort_results(self, results):
        for result in results:
            result['score'] = 0
            periods_etablissement = result.get('periodesEtablissement', [])
            period_etablissement = periods_etablissement[-1] if periods_etablissement else {}
            address = result.get('adresseEtablissement', {})
            legal_entity = result.get('uniteLegale', {})
            if not result.get('dateCreationUniteLegale'):
                result['dateCreationUniteLegale'] = result.get('dateCreationEtablissement', '') or ''
            if self.company_name:
                if legal_entity.get('denominationUniteLegale'):
                    legal_name = legal_entity.get('denominationUniteLegale').lower()
                    if legal_name == self.company_name.lower():
                        result['score'] += 15
                    else:
                        if self.company_name.lower() in legal_name:
                            result['score'] += 5
                        for name_word in legal_name.split(' '):
                            if name_word in self.company_name.lower():
                                result['score'] += 2
                            else:
                                result['score'] -= 1
            if period_etablissement.get('etatAdministratifEtablissement', 'A') == 'A':
                result['score'] += 1

            if result.get('etablissementSiege'):
                result['score'] += 2

            if address.get('codePostalEtablissement') and address.get('codePostalEtablissement') == self.zip_code:
                result['score'] += 5
            elif address.get('codeCommuneEtablissement') and self.department == address.get('codeCommuneEtablissement'):
                result['score'] += 5
            if legal_entity.get('activitePrincipaleUniteLegale')  and legal_entity.get('activitePrincipaleUniteLegale') == self.naf_id.naf_code:
                result['score'] += 3

        results = sorted(results, key=lambda k: (-k['score'], k['dateCreationUniteLegale']))

        return results

    def search_partner(self):
        variable = []
        pattern = []
        if self.company_name:
            name_words = self.company_name.split(' ')
            for name_word in name_words:
                variable.append('denominationUniteLegale')
                pattern.append(name_word)
        if self.zip_code:
            variable.append('codePostalEtablissement')
            pattern.append('"%s"' % self.zip_code)
        if self.department:
            variable.append('codeCommuneEtablissement')
            pattern.append('%s*' % self.department)
        if self.naf_id:
            variable.append('activitePrincipaleUniteLegale')
            pattern.append('"%s"' % self.naf_id.naf_code)
        if self.siret:
            variable.append('siret')
            pattern.append('"%s"' % self.siret)
        if self.siren:
            variable.append('siren')
            pattern.append('"%s"' % self.siren)
        res = self.search_sirene(variable, pattern)
        if res:
            res_values = [(0, 0, self._prepare_result_values(e)) for e in res]
            self.result_count = len(res)
            self.result_ids = [(5,)] + res_values
        else:
            self.result_count = 0
            self.result_ids = [(5,)]

        return {
            'context': self.env.context,
            'name': _('Search Partner in Sirene Database'),
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def _prepare_result_values(self, result):
        res = self.env['search.sirene.result'].sirene_values_to_record_values(result)
        res['model'] = self.model
        return res
