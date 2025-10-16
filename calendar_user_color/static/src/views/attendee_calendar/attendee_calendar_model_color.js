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




patch(AttendeeCalendarModel.prototype, {
    async updateAttendeeData(data) {
        const res = await super.updateAttendeeData(...arguments);

        // Get current user's color (from session)
        const userColor = session.color;
        console.log("user color:", userColor);

        for (const event of Object.values(data.records)) {
            const eventData = event.rawRecord;
            console.log("session.uid:", session.uid);
            console.log("session.partner_id:", session.partner_id);
            console.log("event.ColorIndex:", event.colorIndex);

            console.log("eventData:", eventData);
            console.log("eventData.partner_ids:", eventData.partner_ids)

            // If event has the current user as attendee, use his color
            if (eventData.partner_ids?.includes(session.partner_id)) {
                event.colorIndex = userColor;
            } else {
                // fallback: keep creator's color
                event.colorIndex = eventData.color;
            }
        }
        return res;
    },
});



