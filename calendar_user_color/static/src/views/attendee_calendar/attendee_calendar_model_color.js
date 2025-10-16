/** @odoo-module **/
import { AttendeeCalendarModel } from "@calendar/views/attendee_calendar/attendee_calendar_model";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";



// patch(AttendeeCalendarModel.prototype, {
//   async updateAttendeeData(data) {
//         const res = await super.updateAttendeeData(...arguments);
//         for (const event of Object.values(data.records)) {
//             const eventData = event.rawRecord;
//             event.colorIndex = eventData.color;
//         }
//         return res;
//     },
// });


const partnerColorMap = session.partner_color_map || {};


patch(AttendeeCalendarModel.prototype, {
    async updateAttendeeData(data) {
        const res = await super.updateAttendeeData(...arguments);

        console.log("user colors:", partnerColorMap);

        for (const event of Object.values(data.records)) {
            console.log("event:", event)
            const eventData = event.rawRecord;

            console.log("event.ColorIndex:", event.colorIndex);

            console.log("eventData:", eventData);
            console.log("eventData.partner_ids:", eventData.partner_ids)

            const partnerId = event.attendeeId;
            console.log("partnerId:", partnerId);


            // If event has the current user as attendee, use his color
            // if (eventData.partner_ids?.includes(session.partner_id)) {
            //     event.colorIndex = userColor;
            // } else {
            //     // fallback: keep creator's color
            //     event.colorIndex = eventData.color;
            // }
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



