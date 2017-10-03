import logging
import re

from openerp import api, SUPERUSER_ID

logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    fix_nace_id(env)

def fix_nace_id(env):
    logger.info("[UDPATE res.partner] Correction category_id for nace")
    data_records = env['ir.model.data'].search([
        ('model', '=', 'res.partner.category'),
        ('res_id', '!=', False),
        ('name', 'ilike', 'nace'),
        ('module', '=', 'l10n_eu_nace'),
        ])

    category_model = env['res.partner.category']
    nace_categ_ids = data_records.mapped('res_id')
    nace_categs = category_model.browse(nace_categ_ids)

    res_partners = env['res.partner'].search([
        '|', ('active', '=', True), ('active', '=', False),
        ('category_id', '!=', False),
        #('category_id', 'in', nace_categ_ids)
        ('category_id', 'child_of', nace_categ_ids)
        ])

    for partner in res_partners:
        # if re.match("^\[.*\]", category.name):
        #     nace_code = category.name.split("[")[1].split("]")[0]
        category_ids = category_model.browse()
        for category in partner.category_id:
            if category in nace_categs:
                if re.match("^\[.*\]", category.parent_id.name):
                    nace_code = category.parent_id.name.split("[")[1].split("]")[0]
                    nace = session.env['res.partner.nace'].search([('code', '=', nace_code)])
                    nace.ensure_one()
                    partner.nace_ids |= nace
                    category_ids += category
    category_ids.unlink()
