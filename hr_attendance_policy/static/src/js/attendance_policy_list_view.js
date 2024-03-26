odoo.define('hr_attendance_policy.ControlPanel', function (require) {
    "use strict";

    var core = require('web.core');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');

    var QWeb = core.qweb;

    var AttendancePolicyListView = ListView.extend({
        render_buttons: function($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                let btn = QWeb.render('CreateAttendancePolicyButton', {});
                this.$buttons.prepend(btn);
                this.$buttons.on('click', '.o_button_create_attendance_policy', this.proxy('action_create_attendance_policy'));
            }
        },
        action_create_attendance_policy: function () {
            var self = this;
            this.do_action('hr_attendance_policy.action_open_attendance_policy_form', {
                on_close: function () {
                    self.reload();
                },
            });
        },
    });

    viewRegistry.add('attendance_policy_list_view', AttendancePolicyListView);
});
