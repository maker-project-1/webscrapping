jQuery(document).ready(function () {

    if (document.URL.match("cart.aspx")) {
        return false;
    }
    var $btn_cart = jQuery(".StyleB_Cart_");   
    $btn_cart.unbind("click");
    $btn_cart.bind("click", function (e) {
        
        var goods = "";
        var qty = "";
    
        var $goodsAll = $('input[name=goods]');
        var ga = $goodsAll.map(function(index, el) { return $(this).val(); }).get().join(",");
        
        var $qtyAll = $('input[name=qty]');
        var qa = $qtyAll.map(function(index, el) { return $(this).val(); }).get().join(",");
        
        var goodsArrayData = ga.split(",");
        var qtyArrayData = qa.split(",");
            
        if (goodsArrayData.length == qtyArrayData.length) {
            
            for (i = 0; i < goodsArrayData.length; i++){
            
                if (qtyArrayData[i] != "" && qtyArrayData[i] != 0) {
                    goods += goodsArrayData[i];
                    goods += ",";
                    qty += qtyArrayData[i];
                    qty += ",";
                }
            }
        }
            
        jQuery.ajax({
            async: false,
            type: "POST",
            url: EC_WWW_ROOT + "/shop/js/addcartmulti.aspx",
            data: { "goods": goods, "qty": qty },
            cache: false,
            ifModified: false,
            dataType: "json",
            
            success: function (obj) {
            
                if (!obj.agree) {
                    var arrayData = obj.vars.split(",");
                  
                    for (i = 0; i < arrayData.length; i++){
                        s.addCart(arrayData[i]);
                    }
                    
                    //Cxense script
                    cX.callQueue.push(['invoke', function() {
                        cX.setSiteId(stdvar.SiteId);
                        cX.setEventAttributes({ origin: 'aeo-std-' + stdvar.shop,persistedQueryId:stdvar.persistedQueryId});
                        for (i = 0; i < arrayData.length; i++){
                            var wkStr = arrayData[i].split(":");
                            var wkCategory = new Array();
                            for (j = 1; j < 7; j++){
                                if (wkStr[2].length >= j * 2) {
                                    wkCategory[j] = wkStr[2].substring(0, j * 2);
                                } else {
                                    wkCategory[j] = "";
                                }
                            }
                            cX.sendEvent('CART',{"shop":stdvar.shop,"item_code":wkStr[3],"category1":wkCategory[1],"category2":wkCategory[2],"category3":wkCategory[3],"category4":wkCategory[4],"category5":wkCategory[5],"category6":wkCategory[6]});
                        }
                    }]);
                }
                
                document.forms["frm_search_list"].submit();
                
                return true;
            },
            error: function (xhr, status, thrown) {
                return false;
            }
        });
        
        return true;
    });
});
