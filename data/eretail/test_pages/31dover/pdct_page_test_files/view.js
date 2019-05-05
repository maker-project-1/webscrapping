/*
 * Develop by Anh TO - anh.to87 (@) gmail.com - skype: anh.to87
 * */
window.tableSelectorCart            =   "#shopping-cart-table";
window.tableSelectorCartTotal       =   "#shopping-cart-totals-table";
window.sessionPopupId               =   null;
var view_freegift_init,
    view_freegift_catalog_view,
    view_freegift_checkout_onepage,
    view_freegift_crosssel;

window.view_freegift_cart = null;
window.giftModal = null;

window.staticOverlay = null;
window.staticLoaderGift  = null;
window.processingGift = {
    adding  :{
        product: false,
        gift: false
    },
    cart    : false,
    removing: false
};

window.FreeGift.$(document).ready(function($){
    Backbone.CustomboxView = Backbone.View.extend({
        name: "CustomboxView",
        modalContainer: null,
        defaultOptions: {
            targetContainer: document.body,
            closeClick: true,
            customParentClass: "",
            css:
            {
                "border": "1px solid #fff",
                "background-color": "#fff",
                "-webkit-box-shadow": "0px 0px 8px 1px rgba(0, 0, 0, 0.5)",
                "-moz-box-shadow": "0px 0px 8px 1px rgba(0, 0, 0, 0.5)",
                "box-shadow": "0px 0px 8px 1px rgba(0, 0, 0, 0.5)"
            }
        },
        showModal: function(options){
            this.defaultOptions.targetContainer = document.body;
            this.options = jQuery.extend( true, {}, this.defaultOptions, options, this.options);
            var thisEl = false;
            var $el = jQuery(this.el);
            //var modalContainer = this.ensureModalContainer( this.options.targetContainer).empty();
            $el.addClass( "modal");
            $el.addClass( this.options.customParentClass );
            $el.css( this.options.css);
            jQuery(".custombox-modal", document.body).remove();
            jQuery(document.body).append( $el);
            jQuery.fn.custombox({
                url: '.modal',
                effect:     'fadein',
                position:   'left, right',
                customClass:       this.options.customParentClass,
                complete: function(){
                    jQuery(".modal", document.body).each(function(){
                        if(jQuery(this).parent()[0].tagName == "BODY"){
                            jQuery(this).remove();
                            return false;
                        }
                    });
                },
                close: function(){
                    if(typeof FreeGift != "undefined"){
                        FreeGift.trigger("event:after_close_popup");
                    }
                }
            });
        },
        hideModal: function(){
            jQuery.fn.custombox('close');
        }
    });

    FreeGift.Views.CrossSell        = Backbone.View.extend({
        el: window.FreeGift.$(".crosssell"),
        events: {
            "click .btn-cart": "hdlBtnCart"
        },
        initialize: function(){
            this.$el.find(".btn-cart").each(function(){
                if(window.FreeGift.$(this).is("[onclick]")){
                    if(window.FreeGift.$(this).attr("onclick").indexOf("setLocation") > -1){
                        var data_url = /setLocation\(('?"?)(.*?)('?"?)\)/gi.exec(window.FreeGift.$(this).attr("onclick"));
                        data_url = data_url[2];
                        window.FreeGift.$(this).attr("data-url", data_url);
                        window.FreeGift.$(this).removeAttr("onclick").show();
                    }
                }
            });
        },
        hdlBtnCart: function(ev){
            if(window.processingGift.adding.product){
                return false;
            }

            window.processingGift.adding.product = true;

            var _item = window.FreeGift.$(ev.target).closest('.item');
            var pid = parseInt(_item.find('.mw-hidden-product').attr('data-product-id'));
            var p_tid = _item.find('.mw-hidden-product-type').attr('data-product-type-id');
            var p_has_option = _item.find('.mw-hidden-product-has-options').attr('data-has-options');
            var p_name = _item.find('.product-name > a').text();
            var p_image = _item.find('.mw-hidden-product-image').attr('data-product-image');
            if(_.isNumber(pid) == false){
                return false;
            }
            if(p_tid == 'grouped'){
                location.href = _item.find('.btn-cart').attr("data-url");
                return false;
            }

            var data_post = [];

            if(p_tid == 'simple' && p_has_option == "0"){
                data_post.push({name: 'product', value: pid});
                data_post.push({name: 'ajax_add', value: 1});
                FreeGift.on('event:before_quick_add_to_cart', view_freegift_init.beforeAddToCart);
                FreeGift.on('event:after_quick_add_to_cart', this.afterAddToCart);
                window.giftModal.quickAddToCart({p_name: p_name, p_image: p_image, data: data_post, method: "post"});
            }else{
                var input_hidden = "<input type='hidden' name='ajax_add' value='1'>";
                FreeGift.on('event:before_general_add_to_cart', view_freegift_init.beforeAddToCart);
                FreeGift.on('event:after_general_add_to_cart', this.afterAddToCart);
                window.giftModal.getBox({p_tid: p_tid, pid: pid, p_name: p_name, p_has_option: p_has_option, input_hidden: input_hidden, p_image: p_image, ev: ev, is_gift: false, method: "post"});
            }
            return false;
        },
        beforeAddToCart: function(params){
            return true;
        },
        afterAddToCart: function(params){
            FreeGift.on("event:after_update_cart", view_freegift_crosssel.afterUpdateCart);
            window.staticMinicart = new FreeGift.Views.miniUpdCart();
            return true;
        },
        afterUpdateCart: function(params){
            FreeGift.off("event:after_update_cart");
            window.processingGift.adding.product = false;
            window.processingGift.adding.gift = false;
        }
    });

    FreeGift.Views.CheckoutOnepage  = Backbone.View.extend({
        el: window.FreeGift.$(".freegift_rules_onepage_container, .freegift_rules_banner_onepage_container"),
        initialize: function(){
            if(this.$el.find("#promotion_banner").find("li").length > 1){
                window.FreeGift.$("#promotion_banner").jcarousel({
                    auto: 4,
                    scroll: 1,
                    visible:1,
                    buttonNextHTML: '',
                    buttonPrevHTML: '',
                    wrap: 'last'
                });
            }
            if(this.$el.find("#freegift_rules").find("li").length > 1){
                window.FreeGift.$("#freegift_rules").jcarousel({
                    auto: 4,
                    scroll: 1,
                    visible:1,
                    buttonNextHTML: '',
                    buttonPrevHTML: '',
                    wrap: 'last'
                });
            }
        }
    });

    FreeGift.Views.CatalogView      = Backbone.View.extend({
        el: window.FreeGift.$(".mw-fg-catalog-product, .freegift_catalog_container"),
        initialize: function(){
            if(this.$el.find(".mw-fg-items").length > 0){
                window.FreeGift.$(this.$el.find(".mw-fg-items")).each(function(){
                    var option_tooltip = {
                        contentPosition: 'belowStatic',
                        stayOnContent: true,
                        offset: 0
                    };
                    var aTooltip = window.FreeGift.$(this).find("a[id*=stay-target]");
                    aTooltip.ezpz_tooltip(option_tooltip);
                });
            }
        }
    });

    FreeGift.Views.InitInSlider     = Backbone.View.extend({
        el: window.FreeGift.$("#mw-fg-slider-cart"),
        events: {
            "click button.btn-cart" :   "hdlBtnCart"
        },
        initialize: function(){
            this.$el.find(".btn-cart").each(function(){
                window.FreeGift.$(this).attr("data-url-cart", window.FreeGift.$(this).attr("href"));
                window.FreeGift.$(this).attr("href", "javascript:;");
            });
            this.init();
            this.initPromotionBanner();
            this.initPromotionMessage();
        },
        hdlBtnCart: function(ev){
            var _item = window.FreeGift.$(ev.target).closest('.mw-fg-items');
            var _button = _item.find("button.btn-cart");
            var pid = parseInt(_item.find('.mw-hidden-product').attr('data-product-id'));
            var p_tid = _item.find('.mw-hidden-product-type').attr('data-product-type-id');
            var p_has_option = _item.find('.mw-hidden-product-has-options').attr('data-has-options');
            var p_name = _item.find('.product-name > a').text();
            var p_image = _item.find('.mw-hidden-product-image').attr('data-product-image');
            if(_.isNumber(pid) === false){
                return false;
            }
            var input_hidden = "<input type='hidden' name='ajax_gift' value='1'>";
            var data_post = [];
            switch(_button.attr('data-ffg-type')){
                case 'catalog':
                    input_hidden += "<input type='hidden' name='free_catalog_gift' value='"+_button.attr('data-catalog-gift')+"'>\n";
                    input_hidden += "<input type='hidden' name='applied_catalog_rule' value='"+_button.attr('data-applied-catalog-rule')+"'>\n";
                    data_post.push({name: 'free_catalog_gift' , value: _button.attr('data-catalog-gift')});
                    data_post.push({name: 'applied_catalog_rule' , value: _button.attr('data-applied-catalog-rule')});
                    break;
                case 'sale':
                    input_hidden += "<input type='hidden' name='apllied_rule' value='"+_button.attr('data-applied-rule')+"'>\n";
                    input_hidden += "<input type='hidden' name='freegift' value='1'>\n";
                    data_post.push({name: 'apllied_rule' , value: _button.attr('data-applied-rule')});
                    data_post.push({name: 'freegift' , value: 1});
                    break;
                case 'coupon':
                    input_hidden += "<input type='hidden' name='freegift_with_code' value='1'>\n";
                    input_hidden += "<input type='hidden' name='apllied_rule' value='"+_button.attr('data-rule-id')+"'>\n";
                    input_hidden += "<input type='hidden' name='freegift_coupon_code' value='"+_button.attr('data-freegift-code')+"'>\n";
                    data_post.push({name: 'freegift_with_code' , value: 1});
                    data_post.push({name: 'apllied_rule' , value: _button.attr('data-rule-id')});
                    data_post.push({name: 'freegift_coupon_code' , value: _button.attr('data-freegift-code')});
                    break;
            }

            this.undelegateEvents();
            _item.css("opacity", "0.2");
            window.sessionPopupId = _item;
            FreeGift.on("event:after_close_popup", this.afterClosePopup);
            window.processingGift.adding.gift = true;
            if(p_tid == 'simple' && p_has_option == "0"){
                data_post.push({name: 'product', value: pid});
                data_post.push({name: 'ajax_gift', value: 1});
                FreeGift.on('event:before_quick_add_to_cart', this.beforeAddToCart);
                FreeGift.on('event:after_quick_add_to_cart', this.afterAddToCart);
                window.giftModal.quickAddToCart({p_name: p_name, p_image: p_image, data: data_post});
            }else{
                FreeGift.on('event:before_general_add_to_cart', this.beforeAddToCart);
                FreeGift.on('event:after_general_add_to_cart', this.afterAddToCart);
                window.giftModal.getBox({p_tid: p_tid, pid: pid, p_name: p_name, p_has_option: p_has_option, p_image: p_image, ev: ev, input_hidden: input_hidden, is_gift: true});
            }
        },
        init: function(){
            if(hasGiftProduct){
                var view = this;
                view.setElement(window.FreeGift.$("#mw-fg-slider-cart"));
                view.$el.show();
                var option_tooltip = {
                    contentPosition: 'belowStatic',
                    stayOnContent: true,
                    offset: 0
                };

                if(window.FreeGift.$(".mw-fg-items").length > 0){
                    window.FreeGift.$(".mw-fg-items").each(function(){
                        var aTooltip = window.FreeGift.$(this).find("a[id*=stay-target]");
                        aTooltip.ezpz_tooltip(option_tooltip);
                    });
                    bCarousel.init();

                }else{
                    hasGiftProduct = false;
                }
            }else{

            }
        },
        initPromotionBanner: function(){
            if(hasPromotionBanner){
                if(window.FreeGift.$('.freegift_rules_banner_container').find("#promotion_banner").length > 0){
                    window.FreeGift.$('.freegift_rules_banner_container').show();
                    window.FreeGift.$('#promotion_banner').jcarousel({
                        auto: 2,
                        scroll: 1,
                        visible:1,
                        buttonNextHTML: '',
                        buttonPrevHTML: '',
                        wrap: 'last'
                    });
                }
            }else{
                hasPromotionBanner = false;
                window.FreeGift.$('.freegift_rules_banner_container').hide();
            }
        },
        initPromotionMessage: function(){
            if(hasPromotionMessage){
                if(window.FreeGift.$('.freegift_rules_container').find("#freegift_rules").length > 0){
                    window.FreeGift.$('.freegift_rules_container').show();
                    window.FreeGift.$('#freegift_rules').jcarousel({
                        auto: 2,
                        scroll: 1,
                        visible:1,
                        buttonNextHTML: '',
                        buttonPrevHTML: '',
                        wrap: 'last'
                    });
                }
            }else{
                hasPromotionMessage = false;
                window.FreeGift.$('.freegift_rules_container').hide();
            }
        },
        beforeAddToCart: function(params){
            window.sessionPopupId = null;
            if(window.FreeGift.$(tableSelectorCart).find("tbody").find("tr").length > 0){
                /** If template checkout cart using tbody->tr */
                var tBody       = window.FreeGift.$(tableSelectorCart).find("tbody");
                var newTtr      = tBody.find("tr:last-child").clone();
                var countCol    = newTtr.find("td").length;
                var colIndexImage   = view_freegift_init.findCol(newTtr, ".product-image");
                var colIndexName    = view_freegift_init.findCol(newTtr, ".product-name");
                var colImage        = newTtr.find("td:eq("+colIndexImage+")");
                var colName         = newTtr.find("td:eq("+colIndexName+")");
                view_freegift_init.resetCol(newTtr);

                colImage.html('<a href="javascript:;" title="'+params.p_name+'" class="product-image"><img src="'+params.image+'" width="75" height="75"/></a>');
                colName.html('<h2 class="product-name adding"><a href="javascript:;">'+params.p_name+'</a><br /></h2>');
                colName.append('<span class="product-adding">'+Translator.translate('Adding...')+'</span>');

                newTtr.attr("id", "item_adding_"+params.session_id);
                tBody.find("tr:last-child").removeClass("last even odd").addClass();
                tBody.append(newTtr);
                view_freegift_init.resetRow(tBody.find("tr"));
                window.staticLoaderGift.overlayShow({text: "Adding product to cart..."});

                FreeGift.off('event:before_quick_add_to_cart');
                FreeGift.off('event:before_general_add_to_cart');
            }else{
                /** Otherwise then after ajax, reload checkout cart */
            }
        },
        afterAddToCart: function(params){
            var data = params.data;
            var session_id = params.session_id;
            window.staticLoaderGift.overlayHide();
            window.processingGift.adding.gift = false;
            if(window.FreeGift.$(tableSelectorCart).find("tbody").find("tr").length > 0){
                if(data.error == 0){
                    var tBody       = window.FreeGift.$(tableSelectorCart).find("tbody");
                    tBody.find("tr#item_adding_"+session_id).remove();
                    tBody.append(data.item_html);

                    if(typeof data.freegift != 'undefined'){
                        if(window.FreeGift.$.trim(data.freegift) == ""){
                            window.FreeGift.$("#mw-fg-slider-cart:eq(0)").html("");
                        }else{
                            window.FreeGift.$("#mw-fg-slider-cart").html("");
                            window.FreeGift.$("#mw-fg-slider-cart").after(data.freegift);
                            window.FreeGift.$("#mw-fg-slider-cart:eq(0)").remove();

                            view_freegift_init.init();
                        }
                    }
                }else{
                    window.FreeGift.$(".mw-fg-items").each(function(){
                        window.FreeGift.$(this).css("opacity", "1");
                    });

                    var tBody       = window.FreeGift.$(tableSelectorCart).find("tbody");
                    tBody.find("tr[id*=item_adding]").each(function(){
                        window.FreeGift.$(this).remove();
                    });
                    alert(data.message);
                }
                FreeGift.off('event:after_quick_add_to_cart');
                FreeGift.off('event:after_general_add_to_cart');
            }
        },
        afterClosePopup: function(){
            if(window.sessionPopupId != null){
                window.sessionPopupId.css("opacity", "1");
                FreeGift.off("event:after_close_popup");
                FreeGift.off('event:before_quick_add_to_cart');
                FreeGift.off('event:before_general_add_to_cart');

                FreeGift.off('event:after_quick_add_to_cart');
                FreeGift.off('event:after_general_add_to_cart');
                window.sessionPopupId = null;
                view_freegift_init.delegateEvents();
            }
        },
        /**
         * pel: parent element
         * el : element need to find
         * */
        findCol: function(pel, el){
            var index = 0;
            pel.find("td").each(function(k, v){
                if(window.FreeGift.$(this).find(el).length > 0){
                    index = k;
                    return;
                }
            });
            return index;
        },
        resetCol: function(pel){
            pel.find("td").each(function(){
                window.FreeGift.$(this).html("");
            });
        },
        resetRow: function(pel){
            var count = 1;
            pel.each(function(){
                window.FreeGift.$(this).removeClass("odd even");
                window.FreeGift.$(this).addClass((count%2 == 0 ? "even" : "odd"));
                count++;
            });
        }
    });

    FreeGift.Views.modal            = Backbone.CustomboxView.extend({
        _params: "",
        tmpl: window.FreeGift.$("#mwFreeGiftModal").html(),
        events: {
            "click button.btn-cart": "_addToCart",
            "click .close": "hide"
        },
        renderBox:function(params)  {
            if(typeof params == "undefined"){
                return false;
            }

            params.title = (typeof params.title == 'undefined') ? '' : params.title;
            params.content = (typeof params.content == 'undefined') ? '' : params.content;
            params.input_hidden = (typeof params.input_hidden == 'undefined') ? '' : params.input_hidden;
            params.custom_parent_class = (typeof params.custom_parent_class == 'undefined') ? '' : params.custom_parent_class;
            params.header_class_size = (typeof params.header_class_size == 'undefined') ? '' : params.header_class_size;
            params.controller = (typeof params.controller == 'undefined') ? '' : params.controller;
            params.callback = (typeof params.callback == 'undefined') ? '' : params.callback;
            this._params = params;
            this.template = _.template(this.tmpl);
            this.render(params);
            var options_modal = {closeClick: false, customParentClass: params.custom_parent_class + " " + params.header_class_size};

            switch(params.custom_parent_class){
                case 'bundle':
                    options_modal.y = 80;
                    break;
                case 'grouped':
                    options_modal.y = 220;
                    break;
                default:
                    break;
            }
            this.showModal(options_modal);
            FreeGift.trigger("event:after_show_modal", params);
            this.setElement(window.FreeGift.$(".custombox-modal"));
        },
        hide: function(){
            this.hideModal();
        },
        render:function(params){
            this.$el.html( this.template(params));
            return this;
        },
        beforeShow: function(params){

        },
        _addToCart: function(ev){
            FreeGift.on("event:after_close_popup", this.afterClosePopup);
            var productAddToCartForm = new VarienForm('product_addtocart_modal_form');
            if (productAddToCartForm.validator.validate()) {
                if(ev.delegateTarget.className.indexOf("simple") > -1){
                    this.generalAddToCart(ev, "simple");
                }else if(ev.delegateTarget.className.indexOf("configurable") > -1){
                    this.generalAddToCart(ev, "configurable");
                }else if(ev.delegateTarget.className.indexOf("bundle") > -1){
                    this.generalAddToCart(ev, "bundle");
                }else if(ev.delegateTarget.className.indexOf("grouped") > -1){
                    this.generalAddToCart(ev, "grouped");
                }else if(ev.delegateTarget.className.indexOf("virtual") > -1){
                    this.generalAddToCart(ev, "virtual");
                }else if(ev.delegateTarget.className.indexOf("downloadable") > -1){
                    this.generalAddToCart(ev, "downloadable");
                }
            }else{
                var api = window.pane.data('jsp');
                api.reinitialise();
            }
        },
        afterClosePopup: function(){
            FreeGift.off("event:after_close_popup");
            FreeGift.off('event:before_quick_add_to_cart');
            FreeGift.off('event:before_general_add_to_cart');
            view_freegift_init.delegateEvents();
        },
        quickAddToCart: function(params){
            if(typeof params == "undefined"){
                return false;
            }

            params.method = (typeof params.method == "undefined") ? "addg" : params.method;
            console.log('func: quickAddTocart');
            console.log(params.method);
            var view = this;
            var session_id = Math.floor(new Date().getTime() / 1000);
            FreeGift.trigger('event:before_quick_add_to_cart', {session_id: session_id, p_name: params.p_name, image: params.p_image});
            window.FreeGift.$.ajax({
                type : 'POST',
                url  : (params.method == 'post') ? window.freegiftConfig.url.updatePost : window.freegiftConfig.url.add,
                data : params.data,
                dataType: "json",
                success: function(data){
                    if((data == null) || (data != null && data.error == 1)){
                    }else{
                        FreeGift.trigger('event:after_quick_add_to_cart', {data: data, session_id: session_id});
                    }
                },
                complete: function(){
                },
                error: function(){}
            });

            return false;
        },
        generalAddToCart: function(ev, el){
            var thisView = this;
            var data = window.FreeGift.$(".modal."+el).find(".md-"+el+"-product").find("select, input").serializeArray();
            var box = window.FreeGift.$(".modal."+el);
            var image = thisView.$el.find('div.image > img').attr('src');

            var session_id = Math.floor(new Date().getTime() / 1000);
            var pid = window.FreeGift.$(".modal."+el).find(".md-"+el+"-product").find("input[name=product]").val();
            var p_name = window.FreeGift.$(".modal."+el).find(".md-"+el+"-product").find("h3").text();
            var qty = parseInt(this.$el.find('#product_qty').val());
            var parent = window.FreeGift.$(ev.target).closest(".actions");
            if(isNaN(qty) || qty < 1){
                qty = 1;
            }

            var action = window.FreeGift.$(".modal."+el).find(".md-"+el+"-product").find("#action").val();
            data.push({name: 'session_id' , value: session_id});
            window.FreeGift.$.ajax(option_submit(ev, el));
            function option_submit(ev, el){
                data = window.FreeGift.$("#product_addtocart_modal_form").serializeArray();
                return {
                    type : 'POST',
                    url  : (thisView._params.is_gift == "true" || thisView._params.is_gift == true) ? window.freegiftConfig.url.add : (thisView._params.action == "view" ? window.freegiftConfig.url.updatePost : window.freegiftConfig.url.configure),
                    data : data,
                    dataType: "json",
                    beforeSend: function(){
                        thisView.undelegateEvents();
                        FreeGift.trigger('event:before_general_add_to_cart', {item_id: thisView._params.item_id,session_id: session_id, p_name: p_name, image: image});
                        thisView.hide();
                    },
                    success: function(data){
                        if((data == null) || (data != null && data.error == 1)){

                        }else{
                            if(typeof data.upd != "undefined" && data.upd == "1"){
                                if(window.FreeGift.$(tableSelectorCart).find("tbody").find("tr").length > 0){
                                    var tBody       = window.FreeGift.$(tableSelectorCart).find("tbody");
                                    tBody.find("tr#item_"+data.item_id).after(data.item_html);
                                    tBody.find("tr#item_"+data.item_id+":eq(0)").remove();
                                    /** update cart */
                                }
                            }
                            data.p_name = p_name;
                            data.image  = image;
                            FreeGift.trigger('event:after_general_add_to_cart', {data: data, session_id: session_id});
                        }
                    },
                    complete: function(){
                    },
                    error: function(){}
                }
            }

            return false;
        },
        getBox: function(params){
            var view = this;
            FreeGift.trigger('event_before_show_box', params);
            try{
                params.action = (typeof params.action == 'undefined') ? 'view' : params.action;
                params.iid = (typeof params.iid == 'undefined') ? 0 : parseInt(params.iid);
                params.is_gift = (typeof params.is_gift == 'undefined') ? "false" : params.is_gift;
                params.method = (typeof params.method == 'undefined') ? "addg" : params.method;
                switch(params.p_tid){
                    case 'simple':
                        if(params.p_has_option == "1"){
                            var template = _.template(window.FreeGift.$("#freegiftSimpleProduct").html());
                            var template_opt = template({title: params.p_name, product_id: params.pid, image: params.p_image, options_html: "", action: params.action, item_id: params.iid});

                            FreeGift.on("event:after_show_modal", view.afterShowModal);
                            window.giftModal = new FreeGift.Views.modal();
                            window.giftModal.renderBox({pid: params.pid, title: params.p_name, content: template_opt, custom_parent_class: params.p_tid, header_class_size: "medium", controller: params.controller, input_hidden: params.input_hidden, is_gift: params.is_gift, item_id: params.iid, action: params.action, p_tid: params.p_tid, method: params.method});
                        }else{
                            view.quickAddToCart(params);
                            return false;
                        }
                        break;
                    case 'virtual':
                        var template = _.template(window.FreeGift.$("#freegiftVirtualProduct").html());
                        var template_opt = template({title: params.p_name, product_id: params.pid, image: params.p_image, options_html: "", action: params.action, item_id: params.iid});

                        FreeGift.on("event:after_show_modal", view.afterShowModal);
                        window.giftModal = new FreeGift.Views.modal();
                        window.giftModal.renderBox({pid: params.pid, title: params.p_name, content: template_opt, custom_parent_class: params.p_tid, header_class_size: "medium", controller: params.controller, input_hidden: params.input_hidden, is_gift: params.is_gift, item_id: params.iid, action: params.action, p_tid: params.p_tid, method: params.method});
                        break;
                    case 'configurable':
                        var template = _.template(window.FreeGift.$("#freegiftConfigurableProduct").html());
                        var template_opt = template({title: params.p_name, product_id: params.pid, image: params.p_image, options_html: "", action: params.action, item_id: params.iid});

                        FreeGift.on("event:after_show_modal", view.afterShowModal);
                        window.giftModal = new FreeGift.Views.modal();
                        window.giftModal.renderBox({pid: params.pid, title: params.p_name, content: template_opt, custom_parent_class: params.p_tid, header_class_size: "medium", controller: params.controller, input_hidden: params.input_hidden, is_gift: params.is_gift, item_id: params.iid, action: params.action, p_tid: params.p_tid, method: params.method});
                        break;
                    case 'bundle':
                        var template = _.template(window.FreeGift.$("#freegiftTmplBundleProduct").html());
                        var template_opt = template({title: params.p_name, product_id: params.pid, image: params.p_image, options_html: "", action: params.action, item_id: params.iid});

                        FreeGift.on("event:after_show_modal", view.afterShowModal);
                        window.giftModal = new FreeGift.Views.modal();
                        window.giftModal.renderBox({pid: params.pid, title: params.p_name, content: template_opt, custom_parent_class: params.p_tid, header_class_size: "large", controller: params.controller, input_hidden: params.input_hidden, is_gift: params.is_gift, item_id: params.iid, action: params.action, p_tid: params.p_tid, method: params.method});
                        break;
                    case 'downloadable':
                        var template = _.template(window.FreeGift.$("#freegiftDownloadableProduct").html());
                        var template_opt = template({title: params.p_name, product_id: params.pid, image: params.p_image, options_html: "", action: params.action, item_id: params.iid});

                        FreeGift.on("event:after_show_modal", view.afterShowModal);
                        window.giftModal = new FreeGift.Views.modal();
                        window.giftModal.renderBox({pid: params.pid, title: params.p_name, content: template_opt, custom_parent_class: params.p_tid, header_class_size: "medium", controller: params.controller, input_hidden: params.input_hidden, is_gift: params.is_gift, item_id: params.iid, action: params.action, p_tid: params.p_tid, method: params.method});
                        break;
                    case 'grouped':
                        var template = _.template(window.FreeGift.$("#freegiftGroupedProduct").html());
                        var template_opt = template({title: params.p_name, product_id: params.pid, image: params.p_image, options_html: "", action: params.action, item_id: params.iid});
                        FreeGift.on("event:after_show_modal", view.afterShowModal);
                        window.giftModal = new FreeGift.Views.modal();
                        window.giftModal.renderBox({pid: params.pid, title: params.p_name, content: template_opt, custom_parent_class: params.p_tid, header_class_size: "medium", controller: params.controller, input_hidden: params.input_hidden, is_gift: params.is_gift, item_id: params.iid, action: params.action, p_tid: params.p_tid, method: params.method});
                        break;
                }
            }catch (e){
            }
        },
        afterShowModal: function(params){
            window.staticLoaderGift = new FreeGift.Views.Loader({action: "show"});
            window.giftModal.gettingProduct({pid: params.pid, p_tid: params.p_tid, action: params.action, iid: params.item_id, is_gift: params.is_gift});
            FreeGift.off("event:after_show_modal");
        },
        gettingProduct: function(params){
            var session_id = Math.floor(new Date().getTime() / 1000);
            var thisEl = this.$el;
            var thisView = this;
            params.pid = (typeof params.pid == 'undefined') ? 0 : params.pid;
            window.FreeGift.$.ajax({
                type : 'POST',
                url  : window.freegiftConfig.url.getproduct,
                data : 'product='+params.pid+'&action='+params.action+'&item_id='+params.iid+'&is_gift='+params.is_gift,
                success: function(data){
                    thisView._afterDone(data, params);
                },
                error: function(){
                }
            });
            return false;
        },
        _afterDone : function(data, params){
            window.FreeGift.$("#mw-loader").html(data);
            window.pane = window.FreeGift.$(".product-options-top").jScrollPane({autoReinitialise: true});
        }
    });
    FreeGift.Views.Social     = Backbone.View.extend({
        el: window.FreeGift.$('#mw_social'),
        events: {
            "click .share-fb"           : "shareFb"
        },
        initialize: function(){
            this.initFB();
//            this.shareTwitter();
            //this.myTwitter();
            this.msieversion();
            FreeGift.on("event:after_update_cart",this.afterUpdateCart);
        },
        afterUpdateCart : function(params){
            if(params.google_plus == 'true'){
                window.FreeGift.$('#mw_social').remove();
            }
            if(params.like_fb == 'true'){
                window.FreeGift.$('#mw_social').remove();
            }
            if(params.share_fb == 'true'){
                window.FreeGift.$('#mw_social').remove();
            }
            if(params.twitter == 'true'){
                window.FreeGift.$('#mw_social').remove();
            }
        },
        callbackgoogle : function(jsonParam){
            if(jsonParam.state =='on'){
                if(window.processingGift.removing) return false;
                if(window.processingGift.adding.gift || window.processingGift.adding.product) return false;
                window.staticMinicart = new FreeGift.Views.miniUpdCart({update: "true", update_social: "true",google_plus : "true" });

            }else{
                if(window.processingGift.removing) return false;
                if(window.processingGift.adding.gift || window.processingGift.adding.product) return false;
                window.staticMinicart = new FreeGift.Views.miniUpdCart({update: "true", update_social: "true",google_plus : "false" });
            }
        },
        shareFb : function(){
            var _self = this;
            var main_url = window.FreeGift.$('#freegift_share_fb').val();
            var default_message = window.FreeGift.$('#freegift_default_message').val();

            FB.ui(
                {
                    method: 'feed',
                    caption: default_message,
                    link: main_url
                },
                function(response) {
                    if (response && !response.error_code) {
                        _self.shareFbSuccess();

                    } else {
                        _self.shareFbError();
                    }
                }
            );
        },
        shareFbSuccess : function(){
            if(window.processingGift.removing) return false;
            if(window.processingGift.adding.gift || window.processingGift.adding.product) return false;
            window.staticMinicart = new FreeGift.Views.miniUpdCart({update: "true",share_fb : "true" });
        },
        shareFbError : function(){
            if(window.processingGift.removing) return false;
            if(window.processingGift.adding.gift || window.processingGift.adding.product) return false;
            window.staticMinicart = new FreeGift.Views.miniUpdCart({update: "true",share_fb : "false" });
        },
        msieversion : function() {
                var ua = window.navigator.userAgent;
                var msie = ua.indexOf("MSIE ");
                if (msie > 0 || !!navigator.userAgent.match(/Trident.*rv\:11\./)){
                       // If Internet Explorer, return version number
                       //alert(parseInt(ua.substring(msie + 5, ua.indexOf(".", msie))));
                       //console.log('trinh duyet ie');
                }
                else {
                    // If another browser, return 0
                    //alert('otherbrowser');
                    //console.log('khong phai ie');
                    this.myTwitter();
                }
        },
        myTwitter : function(){
            var _self = this;

            window.twttr = (function (d, s, id) {
                var t, js, fjs = d.getElementsByTagName(s)[0];
                if (d.getElementById(id)) return;
                js = d.createElement(s); js.id = id;
                js.src= "https://platform.twitter.com/widgets.js";
                fjs.parentNode.insertBefore(js, fjs);

                return window.twttr || (t = { _e: [], ready: function (f) { t._e.push(f) } });
            }(document, "script", "twitter-wjs"));


            twttr.ready(function(twttr) {
                var url_twitter  = window.FreeGift.$.trim(window.FreeGift.$('#freegift_share_tiwtter').val());
                var freegift_default_message = window.FreeGift.$.trim(window.FreeGift.$('#freegift_default_message').val());
                if(url_twitter!=''){
                    twttr.widgets.createShareButton(
                        url_twitter,
                        document.getElementById('share-twitter'), {
                            url: url_twitter,
                            //count: 'none',
                            text: freegift_default_message,
                            size: 'normal'
                            //hashtags: 'your hashtag'
                        }).then(function(el) {
                            console.log("Twitter Button created.")
                        });
                    twttr.events.bind('tweet', function(event) {
                        //add ur post tweet stuff here
                        console.log('tweet thanh cong');
                        _self.twitterSuccess();
                    });
                }


            });
        },
        shareTwitter : function(){
            var _self = this;
            //window.twttr=(function(d,s,id){var t,js,fjs=d.getElementsByTagName(s)[0];if(d.getElementById(id)){return}js=d.createElement(s);js.id=id;js.src="https://platform.twitter.com/widgets.js";fjs.parentNode.insertBefore(js,fjs);return window.twttr||(t={_e:[],ready:function(f){t._e.push(f)}})}(document,"script","twitter-wjs"));
            twttr.events.bind(
                'tweet',
                function (event) {
                    _self.twitterSuccess();
                }
            );
        },
        twitterSuccess : function(){
            if(window.processingGift.removing) return false;
            if(window.processingGift.adding.gift || window.processingGift.adding.product) return false;
            window.staticMinicart = new FreeGift.Views.miniUpdCart({update: "true",twitter : "true" });
        },
        initFB : function(){
            var _self = this;
            var facebook_app_id = window.FreeGift.$('#mw_freegift_fb').val();
            window.fbAsyncInit = function() {
                FB.init({
                    appId      : facebook_app_id,
                    xfbml      : true,
                    version    : 'v2.1'
                });
                FB.Event.subscribe('edge.create', _self.likeFBcallback);
                FB.Event.subscribe('edge.remove', _self.unlikeFBcallback);
            };


            (function(d, s, id){
                var js, fjs = d.getElementsByTagName(s)[0];
                if (d.getElementById(id)) {return;}
                js = d.createElement(s); js.id = id;
                js.src = "//connect.facebook.net/en_US/sdk.js";
                fjs.parentNode.insertBefore(js, fjs);
            }(document, 'script', 'facebook-jssdk'));
        },
        likeFBcallback : function(url, html_element) {
            if(window.processingGift.removing) return false;
            if(window.processingGift.adding.gift || window.processingGift.adding.product) return false;
            window.staticMinicart = new FreeGift.Views.miniUpdCart({update: "true",like_fb : "true" });
        },
        unlikeFBcallback : function(url, html_element) {
            if(window.processingGift.removing) return false;
            if(window.processingGift.adding.gift || window.processingGift.adding.product) return false;
            window.staticMinicart = new FreeGift.Views.miniUpdCart({update: "true",like_fb : "false" });
        }

    });
    FreeGift.Views.CheckoutCart     = Backbone.View.extend({
        el: window.FreeGift.$(window.tableSelectorCart),
        events: {
            "click a.sc-edit"           : "hdlEdit",
            "click a.btn-remove"        : "hdlRemove",
            "click .btn-update"         : "hdlUpdate"
        },
        initialize: function(){

        },
        hdlEdit: function(ev){
            var item_id = window.FreeGift.$(ev.target).attr("data-item-id");
            var pid = window.FreeGift.$(ev.target).attr("data-product-id");
            var p_tid = window.FreeGift.$(ev.target).attr("data-type-id");
            var p_has_option = window.FreeGift.$(ev.target).attr("data-has-options");
            var p_name = window.FreeGift.$(ev.target).attr("data-product-name");
            var p_image = window.FreeGift.$(ev.target).attr("data-product-image");
            if(p_tid == "simple"){
                if(p_has_option == 0){
                    window.FreeGift.$(ev.target).closest('tr').find(".qty").focus().select();
                    return false;
                }
            }
            if(window.FreeGift.$(ev.target).attr("data-ffg-type") != undefined){
                var is_gift = false;
                var input_hidden = "<input type='hidden' name='ajax_gift' value='1'>\n";
                input_hidden    += "<input type='hidden' name='upd' value='1'>\n";
                input_hidden    += "<input type='hidden' name='item_id' value='"+item_id+"'>\n";
                is_gift = true;

                switch(window.FreeGift.$(ev.target).attr('data-ffg-type')){
                    case 'catalog':
                        input_hidden += "<input type='hidden' name='free_catalog_gift' value='1'>\n";
                        break;
                    case 'sale':
                        input_hidden += "<input type='hidden' name='freegift' value='1'>\n";
                        break;
                    case 'coupon':
                        input_hidden += "<input type='hidden' name='freegift_with_code' value='1'>\n";
                        break;
                }
            }
            FreeGift.on('event:before_general_add_to_cart', this.beforeAddToCart);
            FreeGift.on('event:after_general_add_to_cart', this.afterAddToCart);
            if(p_tid == 'configurable' || p_tid == 'bundle' || p_tid == 'downloadable' || p_tid == 'virtual'){
                window.giftModal.getBox({p_tid: p_tid, pid: pid, p_name: p_name, p_has_option: p_has_option, p_image: p_image, ev: ev, input_hidden: input_hidden, action: "configure", iid: item_id, is_gift: is_gift});
            }
            return false;
        },
        beforeAddToCart: function(params){
            FreeGift.off('event:before_quick_add_to_cart');
            FreeGift.off('event:before_general_add_to_cart');
            window.sessionPopupId = null;
            if(window.FreeGift.$(tableSelectorCart).find("tbody").find("tr").length > 0){
                /** If template checkout cart using tbody->tr */
                var tBody       = window.FreeGift.$(tableSelectorCart).find("tbody");
                var newTtr      = tBody.find("tr[id=item_"+params.item_id+"]");
                var countCol    = newTtr.find("td").length;
                var colIndexImage   = view_freegift_init.findCol(newTtr, ".product-image");
                var colIndexName    = view_freegift_init.findCol(newTtr, ".product-name");
                var colImage        = newTtr.find("td:eq("+colIndexImage+")");
                var colName         = newTtr.find("td:eq("+colIndexName+")");
                view_freegift_init.resetCol(newTtr);

                colImage.html('<a href="javascript:;" title="'+params.p_name+'" class="product-image"><img src="'+params.image+'" width="75" height="75"/></a>');
                colName.html('<h2 class="product-name adding"><a href="javascript:;">'+params.p_name+'</a><br /></h2>');
                colName.append('<span class="product-adding">'+Translator.translate('Updating...')+'</span>');
            }
        },
        afterAddToCart: function(params){
            var data = params.data;
            if(window.FreeGift.$(tableSelectorCart).find("tbody").find("tr").length > 0){
                var tBody       = window.FreeGift.$(tableSelectorCart).find("tbody");
                tBody.find("tr#item_"+data.item_id).after(data.item_html);
                tBody.find("tr#item_"+data.item_id+":eq(0)").remove();
            }
            FreeGift.off('event:after_general_add_to_cart');
        },
        hdlRemove: function(ev){
            if(window.processingGift.cart) return false;
            var view = this;
            ev.preventDefault();

            window.FreeGift.$(ev.target).hide();
            if(window.FreeGift.$(ev.target).attr("href").indexOf('delete/id') > -1){
                var item_id = parseInt(window.FreeGift.$(ev.target).attr('href').split('delete/id/')[1]);
                var url = window.FreeGift.$(ev.target).attr("href").split("cart/delete/")[1];
            }else{
                var item_id = parseInt(window.FreeGift.$(ev.target).attr('data').split('delete/id/')[1]);
                var url = window.FreeGift.$(ev.target).attr("data").split("cart/delete/")[1];
            }
            window.FreeGift.$(ev.target).parent().attr('id', 'rem_'+item_id);
            window.staticLoaderGift = new FreeGift.Views.Loader({action: "show", show_text: false, el: 'rem_'+item_id, size: 15});
            window.staticLoaderGift.overlayShow({text: "Removing product..."});
            view.beforeRemoveCart();
            window.FreeGift.$.ajax({
                type : 'POST',
                url  : window.freegiftConfig.url.delete + url,
                data : 'ajax=true',
                dataType: 'json',
                success: function(data){
                    if(data.error == "1"){

                    }else{
                        window.FreeGift.$(ev.target).closest('tr').slideUp();
                        FreeGift.on("event:after_update_cart", view.afterUpdateCart);
                        window.staticMinicart = new FreeGift.Views.miniUpdCart();
                    }
                }
            });
            return false;
        },
        hdlUpdate: function(ev){
            if(window.processingGift.removing) return false;
            if(window.processingGift.adding.gift || window.processingGift.adding.product) return false;
            window.staticMinicart = new FreeGift.Views.miniUpdCart({update: "true", ev: ev});
            return false;
        },
        beforeRemoveCart: function(){
            view_freegift_init.undelegateEvents();
            window.processingGift.removing = true;
        },
        afterUpdateCart: function(params){
            FreeGift.off("event:after_update_cart");
            view_freegift_init.delegateEvents();
            window.processingGift.removing = false;
        }
    });

    FreeGift.Views.miniUpdCart      = Backbone.View.extend({
        el: window.FreeGift.$("body"),
        summary_qty: false,
        initialize: function(params){

            if(typeof params == "undefined"){
                var params = {};
            }
            if(window.FreeGift.$("#shopping-cart-table").length == 0){
                return;
            }
            if(window.processingGift.cart == false){
                this.process(params);
            }
        },
        process: function(params){
            var form = window.FreeGift.$("#shopping-cart-table").closest('form');
            var data = [];
            if(params.update == "true"){
                data = form.find("input").serializeArray();
                data.push({name: "update_cart_action", value: form.find("button[name=update_cart_action]").val()});
                if(typeof params.google_plus != 'undefined'){
                    data.push({name: "google_plus", value: params.google_plus });
                }
                if(typeof params.like_fb != 'undefined'){
                    data.push({name: "like_fb", value: params.like_fb });
                }
                if(typeof params.share_fb != 'undefined'){
                    data.push({name: "share_fb", value: params.share_fb });
                }
                if(typeof params.twitter != 'undefined'){
                    data.push({name: "twitter", value: params.twitter });
                }
            }

            data.push({name: "ajax_gift", value: "true"});
            data.push({name: "type", value: "checkout_cart"});

            var thisView = this;
            window.processingGift.cart = true;

            window.staticLoaderGift.overlayShow({text: "Updating cart..."});
            view_freegift_init.undelegateEvents();
            window.FreeGift.$.ajax({
                type : 'POST',
                url  : window.freegiftConfig.url.updatePost,
                data : data,
                dataType: 'json',
                success: function(data){
                    FreeGift.trigger("event:after_update_cart",params);
                    view_freegift_init.delegateEvents();
                    window.staticLoaderGift.overlayHide();
                    if(data.html_items == ""){
                        window.location = window.freegiftConfig.url.cart;
                        return false;
                    }

                    window.FreeGift.$("#shopping-cart-table > tbody").css({'opacity': '1'});
                    window.FreeGift.$("#shopping-cart-table > tbody").html(data.html_items);
                    window.FreeGift.$("#shopping-cart-totals-table > tbody").html(data.html_total);
                    window.FreeGift.$("#shopping-cart-totals-table > tfoot").html(data.html_grand_total);

                    if(typeof data.html_gift != 'undefined'){
                        if(window.FreeGift.$.trim(data.html_gift) == ""){
                            window.FreeGift.$("#mw-fg-slider-cart:eq(0)").html("");
                        }else{
                            window.FreeGift.$("#mw-fg-slider-cart").html("");
                            window.FreeGift.$("#mw-fg-slider-cart").after(data.html_gift);
                            window.FreeGift.$("#mw-fg-slider-cart:eq(0)").remove();

                            view_freegift_init.init();
                        }
                    }

                    if(typeof data.html_gift_banner != 'undefined'){
                        if(window.FreeGift.$.trim(data.html_gift_banner) == ""){
                            window.FreeGift.$(".freegift_rules_banner_container:eq(0)").html("");
                        }else{
                            window.FreeGift.$(".freegift_rules_banner_container").html("");
                            window.FreeGift.$(".freegift_rules_banner_container").after(data.html_gift_banner);
                            window.FreeGift.$(".freegift_rules_banner_container:eq(0)").remove();

                            view_freegift_init.initPromotionBanner();
                        }
                    }

                    if(typeof data.html_gift_quote != 'undefined'){
                        if(window.FreeGift.$.trim(data.html_gift_quote) == ""){
                            window.FreeGift.$(".freegift_rules_container:eq(0)").html("");
                        }else{
                            window.FreeGift.$(".freegift_rules_container").html("");
                            window.FreeGift.$(".freegift_rules_container").after(data.html_gift_quote);
                            window.FreeGift.$(".freegift_rules_container:eq(0)").remove();

                            view_freegift_init.initPromotionMessage();
                        }
                    }
                },
                error: function(){}
            });
        }
    });

    FreeGift.Views.Loader           = Backbone.View.extend({
        initialize:function(params){
            if(typeof params == 'undefined'){
                return false;
            }
            params.el = (typeof params.el == 'undefined') ? 'mw-loader' : params.el
            params.show_text = (typeof params.show_text == 'undefined') ? true : params.show_text
            params.size = (typeof params.size == 'undefined') ? 20 : params.size
            params.color = (typeof params.color == 'undefined') ? window.colorLoading : params.color
            if(params.action == 'hide'){
                this.hide();
                return;
            }
            var cl = new CanvasLoader(params.el);
            cl.setColor('#'+params.color); // default is '#000000'
            cl.setDiameter(params.size); // default is 40 (size)
            cl.setDensity(55); // default is 40
            cl.setRange(0.9); // default is 1.3
            cl.setFPS(34); // default is 24
            cl.show(); // Hidden by default
            if(params.show_text){
                window.FreeGift.$("#"+params.el).append("<div style='text-align: center; color: #757373;'>"+Translator.translate("Please wait..")+".</div>");
            }

        },
        hide: function(params){
            window.FreeGift.$("#"+params.el).remove();
        },
        overlayShow: function(params){
            /*if(window.staticOverlay != null){
             return true;
             }*/
            if(typeof params == 'undefined'){
                var params = {};
            }
            params.text = (typeof params.text == "undefined") ? Translator.translate("Loading"): Translator.translate(params.text);
            FreeGift.on("event:before_create_iosoverlay", this.beforeCreateOverlay);
            if(window.staticOverlay == null){
                window.staticOverlay = iosOverlay({
                    text: params.text,
                    spinner: true
                });
            }else{
                window.staticOverlay.update({
                    /*icon: mw_baseUrl+"js/mw_freegift/lib/iosOverlay/img/check.png",*/
                    text: params.text,
                });
            }

            return false;
        },
        overlayUpdate: function(params){
            if(typeof params == 'undefined'){
                var params = {};
            }

            params.text = (typeof params.text == "undefined") ? Translator.translate("Success"): Translator.translate(params.text);
            window.staticOverlay.update({
                /*icon: mw_baseUrl+"js/mw_freegift/lib/iosOverlay/img/check.png",*/
                text: params.text,
            });
            setTimeout(function(){
                    window.staticOverlay.hide();
                    window.processingGift.cart = false;
                    /*window.staticOverlay = null;*/
                }, 450,
                function(){
                });

        },
        overlayHide: function(){
            setTimeout(function(){
                    window.staticOverlay.hide();
                    window.processingGift.cart = false;
                    /*window.staticOverlay = null;*/
                }, 450,
                function(){
                });
        },
        beforeCreateOverlay: function(){
            if(typeof window.staticOverlay != "undefined" && window.staticOverlay != null){
                window.FreeGift.$(".ui-ios-overlay").removeClass("ios-overlay-show").addClass("ios-overlay-hide");
            }

            FreeGift.off("event:before_create_iosoverlay");
        }
    });

    view_freegift_init              = new FreeGift.Views.InitInSlider();
    view_freegift_crosssel          = new FreeGift.Views.CrossSell();
    view_freegift_catalog_view      = new FreeGift.Views.CatalogView();
    view_freegift_checkout_onepage  = new FreeGift.Views.CheckoutOnepage();
    view_freegift_cart              = new FreeGift.Views.CheckoutCart();
    view_freegift_social            = new FreeGift.Views.Social();

    window.giftModal    = new FreeGift.Views.modal();
    window.staticLoaderGift = new FreeGift.Views.Loader();
});