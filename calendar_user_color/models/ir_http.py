from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    # def session_info(self):
    #     info = super().session_info()
    #     info['color'] = self.env.user.color
    #     return info

    def session_info(self):
        info = super().session_info()
        partners = self.env["res.users"].search_read([], ["partner_id", "color"])
        info["partner_color_map"] = {u["partner_id"][0]: u["color"] for u in partners}
        return info
