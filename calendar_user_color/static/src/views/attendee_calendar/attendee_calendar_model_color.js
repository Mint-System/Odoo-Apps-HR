/** @odoo-module **/
import { CalendarModel } from "@web/views/calendar/calendar_model";
import { AttendeeCalendarModel } from "@calendar/views/attendee_calendar/attendee_calendar_model";
// import { CalendarModel } from "@web/views/calendar/calendar_model";
import { AttendeeCalendarModelColor } from "./calendar_model";
import { CalendarFilterPanel } from "@web/views/calendar/filter_panel/calendar_filter_panel";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { getColor } from "@web/views/calendar/colors";


patch(CalendarModel.prototype, {

    async fetchFilters(resModel, fieldNames) {
        // Add your extra field here
        if (!fieldNames.includes("partner_color")) {
            fieldNames = [...fieldNames, "partner_color"];
        }
        const result = await super.fetchFilters(resModel, fieldNames);
        console.log("filters with partner_color", result);
        return result;
    },
    makeFilterUser(filterInfo, previousFilter, fieldName, rawRecords) {
      console.log("makeFilterUser", filterInfo, previousFilter, fieldName, rawRecords);
        const field = this.meta.fields[fieldName];
        const userFieldName = field.relation === "res.partner" ? "partnerId" : "userId";
        console.log("userFieldName", userFieldName);
        const value = this.user[userFieldName];
        console.log("value", value);
        console.log("this.user", this.user);
        let partnerColor = this.user[userFieldName].color || null;
        console.log("partnerColor", partnerColor);

        console.log("rawRecords", rawRecords);


        let colorIndex = value;
        const rawRecord = rawRecords.find(
            (r) => r[filterInfo.writeFieldName][0] === value
        );

        console.log("rawRecord", rawRecord);

        if (filterInfo.colorFieldName && rawRecord) {
            const colorValue = rawRecord[filterInfo.colorFieldName];
            colorIndex = Array.isArray(colorValue) ? colorValue[0] : colorValue;
        }

        //Add partner_color from rawRecord
        // let partnerColor = undefined;
        if (rawRecord && "partner_color" in rawRecord) {
            partnerColor = rawRecord.partner_color;
        }

        return {
            type: "user",
            recordId: null,
            value,
            label: this.user.name,
            active: previousFilter ? previousFilter.active : true,
            canRemove: false,
            colorIndex,
            hasAvatar: !!value,
            partner_color: partnerColor,
            city: this.user.city
        };
    },
});


patch(AttendeeCalendarModel.prototype, {
  async updateAttendeeData(data) {
        const res = await super.updateAttendeeData(...arguments);
        for (const event of Object.values(data.records)) {
            const eventData = event.rawRecord;
            event.colorIndex = eventData.color;
            // event.colorIndex = 1;
        }
        return res;
    },
});






patch(CalendarFilterPanel.prototype, {
    setup() {
      super.setup();
      this.orm = useService("orm");
      console.log(this.modelClass);
      this.userColors = {};
      this.colorsLoaded = false; 
      // this.loadColors();
    },
    // // get modelClass() {
    // //   return AttendeeCalendarModelColor; // Use the inherited class
    // // },

    // async loadColors() {
    //     const partners = await this.orm.searchRead(
    //         "res.partner",
    //         [],  // or filter only relevant partners (like users)
    //         ["color"]
    //     );
    //     for (const p of partners) {
    //         this.userColors[p.id] = p.color;
    //     }
    //     this.colorsLoaded = true;
    //     this.render(); // re-render once colors are available
    // },
    // render() {
    //     if (!this.colorsLoaded) {
    //         return Promise.resolve(); // prevent rendering until colors are loaded
    //     }
    //     return super.render(...arguments);
    // },
    // willUpdate() {
    //     if (this.colorsLoaded) {
    //         this.render(); // re-render once colors are available
    //     }
    // },
    // onWillRender() {
    //     if (!this.colorsLoaded) {
    //         return Promise.resolve(); // prevent rendering until colors are loaded
    //     }
    // },

    // async getFilterColor(filter) {
    //   if (!this.colorsLoaded) { // Check if colors have been loaded before trying to get the filter color
    //         return super.getFilterColor(...arguments);
    //     }
    //     console.log("filter", filter);
    //     console.log("user color", filter.value);
  
    //     if (filter.value === "all") {
    //       return super.getFilterColor(...arguments);
    //     }
    //     // } else {
    //     //   const userId = filter.value;
    //     //   const result = await this.orm.call("res.partner", "read", [userId, ["color"]]);
    //     //   console.log("result", result);
    //     //   const userColor = result[0].color;
    //     //   return "o_cw_filter_color_" + getColor(userColor);
    //     // }
    //     const userColor = this.userColors[filter.value];
    //     if (userColor !== undefined) {
    //         return "o_cw_filter_color_" + getColor(userColor);
    //     }
    //     return super.getFilterColor(...arguments); 
    // }
    getFilterColor(filter) {
            console.log("filter", filter);
            return filter.colorIndex !== null ? "o_cw_filter_color_" + getColor(filter.colorIndex) : "";
        },

    
});


