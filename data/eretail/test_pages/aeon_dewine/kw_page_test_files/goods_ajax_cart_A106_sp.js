jQuery(document).ready(function () {
    var s_width = 98;
    var l_width = 200;
    var goods = "";
    var qty = "";

    if (document.URL.match("cart.aspx")) {
        return false;
    }
    var $btn_cart = jQuery(".goods_ .btn_cart_");
    $btn_cart.unbind("click");
    $btn_cart.bind("click", function (e) {
        var loadStart = function (elem) {
            var src = jQuery(elem).attr("src");
            var re = new RegExp("^(.+)(\.png|\.gif)$");
            var matches = src.match(re);
            var loadingsrc = "";
        	var overlay = jQuery("<div><img src=\"" + EC_WWW_ROOT + "/img/usr/ajax-loader.gif\" alt=\"\"></div>").addClass("btn_overlay_");
            overlay.width(jQuery(elem).width());
            overlay.height(jQuery(elem).height());
            var position = jQuery(elem).position();
            overlay.css("top", position.top + 13);
            overlay.css("left", position.left + 5);
            overlay.css("position", "absolute");
            overlay.css("line-height", jQuery(elem).height() + "px");
            jQuery(elem).parent().parent().append(overlay);
            return overlay;
        }

        var loadEnd = function (elem, iserror) {
            if (!iserror) {
                var src = jQuery(elem).find("img").attr("src");
                var re = new RegExp("^(.+)_loading(\.png|\.gif)$");
                var matches = src.match(re);
                var loadedsrc = "";
                var issmall = false;
                var box = jQuery("<div></div>").addClass("addcart_overlay_")
                                .append(jQuery("<img>")
                                .attr("src", EC_WWW_ROOT + "/img/usr/cart_complete.gif").attr("alt", ""));
                var position = jQuery(elem).position();
                box.css("top", position.top - 57);
                box.css("left", position.left + 15);
                box.css("position", "absolute");
                jQuery(elem).parent().parent().append(box);
                jQuery(box).fadeIn("normal", function () {
                setTimeout(function () {
                        jQuery(box).fadeOut("normal", function () {
                            jQuery(box).remove();
                            jQuery(elem).remove();
                        });
                    }, 900);
                });
            }
            else {
                jQuery(elem).remove();
            }
        }

        var addCart = function (b, g) {
            var o = loadStart(b);
            jQuery.ajax({
                async: true,
                type: "POST",
                url: EC_WWW_ROOT + "/shop/js/addcart.aspx",
                data: { "goods": goods, "qty": qty },
                cache: false,
                ifModified: false,
                dataType: "json",
                
                success: function (obj) {
                    var msg = obj.msg;
                    if (msg != null) {
                        alert(msg.join("\r\n").replace(/<\/?[^>]+>/gi, ""));
                        loadEnd(o, true);
                        return false;
                    }

                    /// <reference path="s_code.js" />
                    try {
                        if (s && obj.vars) {
                            s.addCart(obj.vars); 
                            //Cxense script
                            var wkStr = obj.vars.split(":");
                            var wkCategory = new Array();
                            for (i = 1; i < 7; i++){
                                if (wkStr[2].length >= i * 2) {
                                    wkCategory[i] = wkStr[2].substring(0, i * 2);
                                } else {
                                    wkCategory[i] = "";
                                }
                            }
                            cX.callQueue.push(['invoke', function() {
                                cX.setSiteId(stdvar.SiteId);
                                cX.setEventAttributes({ origin: 'aeo-std-' + stdvar.shop,persistedQueryId:stdvar.persistedQueryId});
                                cX.sendEvent('CART',{"shop":stdvar.shop,"item_code":wkStr[3],"category1":wkCategory[1],"category2":wkCategory[2],"category3":wkCategory[3],"category4":wkCategory[4],"category5":wkCategory[5],"category6":wkCategory[6]});
                            }]);
                        }
                    } catch(e) {
                    }
                    
                    if (jQuery("div#cart > div.price").length > 0) {
                        var self = function () {
                            jQuery("div#cart > div.price").load(EC_WWW_ROOT + "/shop/js/cart.aspx", function () {
                                setTimeout(function () {
                                    loadEnd(o, false);
                                }, 400);
                            });
                        }
                        self();

                    }
                    else {
                        setTimeout(function () {
                            loadEnd(o, false);
                        }, 400);
                    }
                },
                error: function (xhr, status, thrown) {
                    loadEnd(o, true);
                    alert("セッションの有効期間がきれました。\n" +
                          "誠に恐れ入りますが再度トップページよりのアクセスをお願いいたします。\n\n" +
                          "※当サイトではお客様の情報保護のため、一定時間経過後に接続情報を解除させていただいております。");
                    return false;
                }

            });
            return true;
        }

        var href = jQuery(this).parent().attr("href");
        var re = new RegExp("goods=([0-9A-Za-z_\-]+)");
        var matches = href.match(re);
        
        if (matches.length == 2) {
            goods = matches[1];
        }
        else {
            return true;
        }
    
        var $goodsAll = $('input[name=detaillistgoods]');
        var ga = $goodsAll.map(function(index, el) { return $(this).val(); }).get().join(",");
        
        var $qtyAll = $('[name=detaillistqty]');
        var qa = $qtyAll.map(function(index, el) { return $(this).val(); }).get().join(",");
        
        var goodsArrayData = ga.split(",");
        var qtyArrayData = qa.split(",");
                
        if (goodsArrayData.length == qtyArrayData.length) {
            
            for (i = 0; i < goodsArrayData.length; i++){
            
                if (qtyArrayData[i] != "" && qtyArrayData[i] != 0 && goodsArrayData[i] == goods) {
                    qty = qtyArrayData[i];
                }
            }
        }
        
        if (jQuery("#agree_" + goods).length > 0) {
			if ((jQuery.cookie("GoodsAgree") == null || jQuery.cookie("GoodsAgree") == "display=")) {
	            var btn = this;
	            jQuery("#dialog").dialog("destroy");
	            
	            //2015.01.15 [ashida] AEON de WINE お酒 20歳未満確認対応 -------------------------------------
	            //未ログイン
	            jQuery("#agree_" + goods).css("text-align","left");
	            jQuery("#agree2_" + goods).css("text-align","left");
	            //会員登録のお願いメッセージ表示
	            if(jQuery.cookie("adult") == null || jQuery.cookie("adult") == ""){
		            jQuery("#agree_" + goods).dialog({
		                resizable: false,
		                height: 200,
		                width: 230,
		                modal: false,
		                buttons: {
		                    '　O　K　': function () {
		                        jQuery(this).dialog('close');
		                        //location.href = $("#loginUrl").text();
		                        return false;
		                    }
		                }
		            });
		        //ログイン 20歳未満
		        }else if(jQuery.cookie("adult") == "0"){
		            //年齢確認の同意メッセージ表示
			        jQuery("#agree_" + goods).dialog({
			                resizable: false,
			                height: 200,
			                width: 230,
			                modal: false,
			                buttons: {
			                    '　同意する　': function () {
			                        jQuery(this).dialog('close');
			                        jQuery("#agree2_" + goods).dialog({
		                                resizable: false,
		                                height: 200,
		                                width: 230,
		                                modal: false,
		                                buttons: {
		                                   '　O K　': function () {
		                                       jQuery(this).dialog('close');
		                                       return false;
		                                   }
		                                }
		                            });
			                        return false;
			                    },
			                    '同意しない': function () {
			                        jQuery(this).dialog('close');
			                        return false;
			                    }
			                }
			            });
		        //ログイン 20歳以上
		        }else{
		            //年齢確認の同意メッセージ表示
		            jQuery("#agree_" + goods).dialog({
		                resizable: false,
		                height: 200,
		                width: 230,
		                modal: false,
		                buttons: {
		                    '　同意する　': function () {
		                        jQuery(this).dialog('close');
		                        jQuery.cookie("GoodsAgree", "display=on", { path: "/shop"});
		                        addCart(btn, goods);
		                        return false;
		                    },
		                    '同意しない': function () {
		                        jQuery(this).dialog('close');
		                        return false;
		                    }
		                }
		            });
		        }
		        //----------------------------------------------------------------------------------------------
	        }
	        else {
	            addCart(this, goods);
	            return false;
	        }
        }
        else {
            addCart(this, goods);
            return false;
        }
        return false;
    });
});
