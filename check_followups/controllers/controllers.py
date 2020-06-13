# -*- coding: utf-8 -*-
from openerp import http

# class CheckFollowups(http.Controller):
#     @http.route('/check_followups/check_followups/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/check_followups/check_followups/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('check_followups.listing', {
#             'root': '/check_followups/check_followups',
#             'objects': http.request.env['check_followups.check_followups'].search([]),
#         })

#     @http.route('/check_followups/check_followups/objects/<model("check_followups.check_followups"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('check_followups.object', {
#             'object': obj
#         })