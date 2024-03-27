odoo.define('crm_calendar_event.CalendarView2', function (require) {
"use strict";

var CalendarPopover = require('web.CalendarPopover');
var CalendarRenderer = require('web.CalendarRenderer');
var CalendarView = require('web.CalendarView');
var viewRegistry = require('web.view_registry');

var AttendeeCalendarPopover = CalendarPopover.extend({
    template: 'Calendar.attendee.status.popover1',
    events: _.extend({}, CalendarPopover.prototype.events, {
        'click .o-calendar-attendee-status .dropdown-item': '_onClickAttendeeStatus',
        'click .o_cw_popover_edit2': '_onclick_a',
        'click .o_cw_popover_edit3': '_onclick_state_cancel',

    }),
    /**
     * @constructor
     */
    init: function () {
        var self = this;
        this._super.apply(this, arguments);
        var session = this.getSession();
        // Show status dropdown if user is in attendees list
        this.showStatusDropdown = _.contains(this.event.record.partner_ids, session.partner_id);
        if (this.showStatusDropdown) {
            this.statusColors = {accepted: 'text-success', declined: 'text-danger', tentative: 'text-muted', needsAction: 'text-dark'};
            this.statusInfo = {};
            _.each(this.fields.attendee_status.selection, function (selection) {
                self.statusInfo[selection[0]] = {text: selection[1], color: self.statusColors[selection[0]]};
            });
            this.selectedStatusInfo = this.statusInfo[this.event.record.attendee_status];
        }
        var data = {};
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onClickAttendeeStatus: function (ev) {
        ev.preventDefault();
        var self = this;
        var selectedStatus = $(ev.currentTarget).attr('data-action');
        this._rpc({
            model: 'calendar.event',
            method: 'change_attendee_status',
            args: [this.event.id, selectedStatus],
        }).then(function () {
            self.event.record.attendee_status = selectedStatus;  // FIXEME: Maybe we have to reload view
            self.$('.o-calendar-attendee-status-text').text(self.statusInfo[selectedStatus].text);
            self.$('.o-calendar-attendee-status-icon').removeClass(_.values(self.statusColors).join(' ')).addClass(self.statusInfo[selectedStatus].color);
        });
    },

    _onclick_a :function(ev){
            var self = this;
            ev.preventDefault();
            this._rpc({
                model: 'calendar.event',
                method: 'change_calender_evt',
                args: [this.event.id],
            }).then(function (data) {
                 console.log(data);
                 self.do_action(data);
            });
        },

   _onclick_state_cancel :function(ev){
        var self = this;
        ev.preventDefault();
        this._rpc({
            model: 'calendar.event',
            method: 'change_calender_state_cancel',
            args: [this.event.id],
        }).then(function (data) {
             $(".oe_pager_refresh").click();
        });
    },
});

var AttendeeCalendarRenderer = CalendarRenderer.extend({
    config: _.extend({}, CalendarRenderer.prototype.config, {
        CalendarPopover: AttendeeCalendarPopover,
    }),
});


var AttendeeCalendarView = CalendarView.extend({
    config: _.extend({}, CalendarView.prototype.config, {
        Renderer: AttendeeCalendarRenderer,
    }),
});

viewRegistry.add('crm_attendance_calendar', AttendeeCalendarView);

});
