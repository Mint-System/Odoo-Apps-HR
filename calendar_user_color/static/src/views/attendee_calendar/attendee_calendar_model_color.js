/** @odoo-module **/
import {AttendeeCalendarModel} from "@calendar/views/attendee_calendar/attendee_calendar_model";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";

const partnerColorMap = session.partner_color_map || {};

patch(AttendeeCalendarModel.prototype, {
    async updateAttendeeData(data) {
        const res = await super.updateAttendeeData(...arguments);

        for (const event of Object.values(data.records)) {
            const eventData = event.rawRecord;

            const partnerId = event.attendeeId;

            if (partnerColorMap[partnerId]) {
                event.colorIndex = partnerColorMap[partnerId];
            } else {
                // fallback: event creator’s color or default
                event.colorIndex = eventData.color;
            }
        }
        return res;
    },
});
