odoo.define("hr_attendance_kiosk_mode_color.kiosk", function (require) {
    "use strict";

    var MyAttendances = require("hr_attendance.my_attendances");
    var KioskConfirm = require("hr_attendance.kiosk_confirm");
    var GreetingMessage = require("hr_attendance.greeting_message");
    var KioskMode = require("hr_attendance.kiosk_mode");

    function reset() {
        document.getElementsByClassName('o_action_manager')[0].classList.remove('checked_out')
        document.getElementsByClassName('o_action_manager')[0].classList.remove('checked_in')
    }
    function checkin() {
        document.getElementsByClassName('o_action_manager')[0].classList.remove('checked_out')
        document.getElementsByClassName('o_action_manager')[0].classList.add('checked_in')
    }
    function checkout() {
        document.getElementsByClassName('o_action_manager')[0].classList.add('checked_out')
        document.getElementsByClassName('o_action_manager')[0].classList.remove('checked_in')
    }

    MyAttendances.include({
        init: function (parent, action) {
            this._super.apply(this, arguments);
            reset()
        },
        update_attendance: function() {
            this._super.apply(this, arguments);
            checkin()
        }
    });

    KioskConfirm.include({
        start: function() {
            this._super.apply(this, arguments);
            reset()
        },      
    });

    KioskMode.include({
        start: function() {
            this._super.apply(this, arguments);
            reset()
        },      
    });

    GreetingMessage.include({
        welcome_message: function() {
            this._super.apply(this, arguments);
            checkin()
        },
        farewell_message: function() {
            this._super.apply(this, arguments);
            checkout()
        }
    })

});
