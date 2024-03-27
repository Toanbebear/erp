odoo.define('web_xls.XlsModel', function (require) {
	"use strict";

	var BasicModel = require('web.BasicModel');
	var XlsModel = BasicModel.extend({
		get: function () {
			 var self = this;
	        return {records: this.records,view_fields:this.view_fields,model_name:this.model_name,fields:this.fields,viewID:this.viewID,domain:this.domain};
	    },
	    load: function (params) {
	    	this.fields = params.fields;
	        this.view_fields = params.view_fields ;
	        this.model_name = params.model_name ;
	        this.viewID = params.viewID;
	        return this._load(params);
	    },
	    reload: function (id, params) {
	        return this._load(params);
	    },
	    _load: function (params) {
	        this.domain = params.domain || this.domain || [];
            var self = this;
            return this._rpc({
                model: self.model_name,
                method: 'search_read',
                domain: self.domain,
            })
            .then(function (result) {
                self.records = result;
            });
	        this.records = [];
	        return $.when();
	    },
	    isDirty: function (id) {
	        var isDirty = false;
	        
	        return isDirty;
	    },
	});
	return XlsModel;

});
