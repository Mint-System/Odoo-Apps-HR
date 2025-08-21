/** @odoo-module **/
import { AttendeeCalendarModel } from "@calendar/views/attendee_calendar/attendee_calendar_model";
// import { CalendarModel } from "@web/views/calendar/calendar_model";
import { AttendeeCalendarModelColor } from "./calendar_model";
import { CalendarFilterPanel } from "@web/views/calendar/filter_panel/calendar_filter_panel";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { getColor } from "@web/views/calendar/colors";



patch(AttendeeCalendarModel.prototype, {
  async updateAttendeeData(data) {
        const res = await super.updateAttendeeData(...arguments);
        for (const event of Object.values(data.records)) {
            const eventData = event.rawRecord;
            event.colorIndex = eventData.color;
        }
        return res;
    },
});


patch(CalendarFilterPanel.prototype, {
    setup() {
      super.setup();
      this.orm = useService("orm");
      console.log(this.modelClass);
    },
    get modelClass() {
      return AttendeeCalendarModelColor; // Use the inherited class
    },

    async getFilterColor(filter) {
        console.log("filter", filter);
        console.log("user color", filter.value);
  
        if (filter.value === "all") {
          return super.getFilterColor(...arguments);
        } else {
          const userId = filter.value;
          const result = await this.orm.call("res.partner", "read", [userId, ["color"]]);
          console.log("result", result);
          const userColor = result[0].color;
          return "o_cw_filter_color_" + getColor(userColor);
        }
    }
});


