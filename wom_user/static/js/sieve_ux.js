// sieve_ux.js 
// Copyright (C) 2013-2019 Thibauld Nion
//
// This file is part of WaterOnMars (https://github.com/tibonihoo/wateronmars).
//
// WaterOnMars is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// WaterOnMars is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with WaterOnMars.  If not, see <http://www.gnu.org/licenses/>.
//
//
// Requirements:
// - jquery v1.8.2
// - mousetrap.js v1.1.3
// - wom_base.js
//
// Usage:
// Call prepareKeyBindings() in the head of the page.
// Call activateKeyBindings() at the end of the page.


// Preparation (mostly to set up some global variables)
function prepareKeyBindings()
{
  // keybindings globals
  gMouseTrapDisabled = true;
  gCurrentlyFocusedItem = -1;
  gNumReferences = 0;
  gSyncWithServer = false;
  gWaitingForServerAnswer = false;
  gReadURLs = [];
  gUserCollectionURL = "";
  gNumUnread = 0;
  gInitialNumUnread = 0;
}

// Make sure that the item being slid out is marked as read and that
// the next item and its title are displayed correctly.
function onCarouselSlid() {  
  $(".carousel").carousel("pause");
  // get the index by slicing the "wom-refXXX" id after a len(wom-ref) offset
  var newlyShownItemIdx = parseInt($(".item:visible").attr("id").slice(7));
  var previouslyShownItemIdx = gCurrentlyFocusedItem;
  gCurrentlyFocusedItem  = newlyShownItemIdx;
  if (previouslyShownItemIdx>=0) {
    var referenceId = '#wom-ref'+previouslyShownItemIdx.toString();
    var prevNavItem = "#wom-ref-nav-"+previouslyShownItemIdx.toString();
    $(prevNavItem).removeClass("shown");
    if (newlyShownItemIdx>previouslyShownItemIdx) {
      markAsRead($(referenceId),previouslyShownItemIdx);      
    }
  }
  var navItem = "#wom-ref-nav-"+newlyShownItemIdx.toString();
  $(navItem).addClass("shown");
  ensureCorrectVisibility(navItem,"#wom-title-list");
}


// Make sure the carousel correctly fills the height of the window
function adjustCarouselHeight() 
{
  $(".wom-reference-content").css("height",window.innerHeight-120);
  $("#wom-title-list").css("height",window.innerHeight-40);
}

// Initialize the carousel, activate its controls and plug the right callbacks.
function initializeCarousel()
{
  if (gNumReferences==0)
  {
    $(".carousel-control").hide(); 
    return;
  }
  // first adjustment of the carousel height and make sure that at the
  // next resize the adjusted size is updated
  adjustCarouselHeight();
  window.onresize = function  (event) {adjustCarouselHeight();}
  $(".carousel-control").show(); 
  // show the right "switch" text taking into account that accordion
  // is the default view for non-touch devices
  // add event
  $(".carousel").on('slid.bs.carousel',  function () { onCarouselSlid()});
  $(".carousel").carousel("next");
  gCurrentlyFocusedItem = 0;
  $(".carousel-control.left").on('click',function (){carouselSlideToPrevious()});
  $(".carousel-control.right").on('click',function (){carouselSlideToNext()});
  $(".carousel").swipe({
    swipeLeft:function(event, direction, distance, duration, fingerCount) {
        carouselSlideToNext();
    },
    swipeRight:function(event, direction, distance, duration, fingerCount) {
      carouselSlideToPrevious();
    }
  });
  showWarning("wom-sieve-demo-warning");
}

function switchTitleListDisplay() 
{
  if ($(".wom-title-list-switch.active").length) 
    hideTitleList();
  else 
    showTitleList();
}



function hideTitleList() 
{
  $("#wom-title-list").removeClass("col-md-2");
  $(".carousel").removeClass("col-md-10");
  $("#wom-title-list").addClass("hidden");
  $(".carousel").addClass("col-md-12");  
  $(".wom-title-list-switch").removeClass("active");  
}

function showTitleList() 
{
  $("#wom-title-list").removeClass("hidden");
  $(".carousel").removeClass("col-md-12");
  $("#wom-title-list").addClass("col-md-2");
  $(".carousel").addClass("col-md-10");
  $(".wom-title-list-switch").addClass("active");  
}


// Activation that needs to be called once the page is fully generated
// @param syncWithServer a boolean telling whether the read status
// @param userCollectionURL the url to which new bookmarks should be posted
// @param numUnread the total number of unread items (currently ignored)
// should be synced with the server.
function activateKeyBindings(syncWithServer,userCollectionURL,numUnread)
{
  // keybindings globals
  gCurrentlyFocusedItem = -1;
  gMouseTrapDisabled = false;   
  gNumReferences = $(".wom-reference").length;
  gSyncWithServer = syncWithServer;
  gUserCollectionURL = userCollectionURL;
  // only count the numbe of unread items directly accessible by the
  // user (anything else feels weirder)
  gNumUnread = gNumReferences;
  gInitialNumUnread = gNumUnread;
  $("#wom-sieve-reload").on('click',function (){reloadSieve();});
  initializeCarousel();
  // check if viewed in a touch device (and if so activate the
  // carousel by default) with code taken from http://stackoverflow.com/questions/4817029/whats-the-best-way-to-detect-a-touch-screen-device-using-javascript
  var isTouch = (('ontouchstart' in window) || (navigator.msMaxTouchPoints > 0));
  if (isTouch)
    hideTitleList();
  else
    showTitleList();
}



// Make sure that an element is visible by scrolling the page if
// necessary to make it appear at a comfortable place on the page.
// Note: adapted from http://stackoverflow.com/questions/487073/check-if-element-is-visible-after-scrolling 
function ensureCorrectVisibility(elem,view)
{
  var viewHeight = $(view).height();
  var viewTop = $(view).offset().top;
  var visibilityTopThreshold = viewHeight/4;
  var visibilityBottomThreshold = viewHeight/2;
  var elemTop = $(elem).offset().top - viewTop;
  if ( (elemTop <= visibilityTopThreshold) || (elemTop >= visibilityBottomThreshold) )
  {
    var scrollNewTop = elemTop-(viewHeight/4)+$(view).scrollTop();
    $(view).animate({scrollTop: scrollNewTop}, 400); 
  }
}



// Make sure the server will know that certain items have been read
// @param read_items_urls a list of urls identifying the references
// that must be considered as read.
// @param callback function to be called when the server's answer is received
function updateReadStatusOnServer(read_items_urls, callback) 
{
  if (!gSyncWithServer) return;
  var jsonStr = JSON.stringify({"action": "read","references":read_items_urls})
  var currentURL = window.location.href;
  womRequest("POST", currentURL, "json", jsonStr)
    .done(callback)
    .fail(function () {showWarning("wom-server-sync-problem");});
}


// Send a reference's info to add it to the user's collection
// @param url reference's URL
// @param title reference's title
// @param sourceURL URL of the reference's source
// @param sourceTitle name of the reference's source
// @param callback function to be called when the server's answer is received
function saveBookmarkOnServer (url,title,sourceURL,sourceTitle,callback) 
{
  if (gUserCollectionURL=="") return;
  var jsonStr = JSON.stringify({"url": url, "title" : title, "source_url" : sourceURL, "source_title" : sourceTitle });
  womRequest("POST", gUserCollectionURL, "json", jsonStr)
    .done(callback)
    .fail(function () {showWarning("wom-server-save-failed");});
}

function updateReadingProgress() 
{
  progress = Math.round(100*(gInitialNumUnread-gNumUnread)/gInitialNumUnread);
  elt = $("#wom-sieve-reading-progress .progress-bar")
  elt.attr("aria-valuenow",progress.toString());
  elt.attr("style","width: "+progress.toString()+"%;");
}


// Perform all necessary stuff to indicate that a reference should be
// considered as read.
// Note: will act only if the reference has not be marked as read yet !
// @param refElement the element representing the reference that must
// be marked as read
// @param refIdx the index of this reference (typically as indicated
// in #wom-ref{refIdx}
function markAsRead(refElement,refIdx) {
  if ( gNumReferences>0 && !refElement.hasClass('read') ) { 
    refElement.addClass("read");
    $("#wom-ref-nav-"+refIdx.toString()).addClass('read');
    url_elt = document.getElementById('wom-ref'+refIdx.toString()+"-url");
    // NOTE: calling .href on the element provded to applied a silent encoding (at least on firefox)
    // whereas getAttributes provided an untouched value
    raw_url = url_elt.getAttribute("href")
    gReadURLs.push(raw_url);
    rollingUpdateReadStatusOnServer(true);
    gNumUnread -= 1;
    updateReadingProgress();
  }
}

// Make sure to synchronize the read status of update on the server.
// Will continue to update the status if when the server answers, new
// items have been read.
function rollingUpdateReadStatusOnServer(check_lock) {
  if (!check_lock || !gWaitingForServerAnswer) {
    gWaitingForServerAnswer = true;
    var syncedReadURLS = gReadURLs.slice(0)
    gReadURLs = [];
    // we still upload the full *current* list of read items (if
    // there's more than one it probably means that something went
    // wrong with the latest update)
    updateReadStatusOnServer(syncedReadURLS,function (data) {         
      hideWarning("wom-server-sync-problem");
      if (gReadURLs.length>0) {rollingUpdateReadStatusOnServer(false)} 
      else {gWaitingForServerAnswer=false;} });
  }
}

// Make sure that the user gets a visual feedback indicating that the
// reference has been saved.
// @param refIdx the index of this reference (typically as indicated
// in #wom-ref{refIdx}
function markAsSaved(refIdx) {
  var refIdxStr = refIdx.toString();
  var refElement = $('#wom-ref'+refIdxStr);
  if ( !refElement.hasClass('saved') ) { 
    var url = document.getElementById('wom-ref'+refIdxStr+'-url').href;
    var title = document.getElementById('wom-ref'+refIdxStr+'-url').title;
    var sourceURL = document.getElementById('wom-ref'+refIdxStr+'-source-url').href;
    var sourceTitle = document.getElementById('wom-ref'+refIdxStr+'-source-url').title;
    saveBookmarkOnServer(url,title,sourceURL,sourceTitle, function(data) {refElement.addClass("saved");});
  };
}


// Keybinding activation

function carouselSlideToPrevious() 
{
  if (gCurrentlyFocusedItem>0) 
  {
    $(".carousel").carousel("prev");
  }
  return true;
}

// Show previous item
Mousetrap.bind('p', function() { 
  carouselSlideToPrevious();
  if(gMouseTrapDisabled) {return false;}
  gMouseTrapDisabled = true;
  var unfocusedItemIdx = gCurrentlyFocusedItem;
  if (unfocusedItemIdx <= 0)
  {
    // special case: we're at the begining of the list, and we want to
    // make sure that the browsing will restart with the first item.
    gCurrentlyFocusedItem = -1;
    gMouseTrapDisabled = false;
  }
});

function carouselSlideToNext() 
{
  if (gCurrentlyFocusedItem>=gNumReferences-1) 
  {
    var idx = (gNumReferences-1);
    var referenceId = '#wom-ref' + idx.toString();
    markAsRead($(referenceId),idx);
    $('#wom-sieve-reload-message').modal('show')
  }
  else 
  {
    $(".carousel").carousel("next");
  }
  return true;
}

// Show next item
Mousetrap.bind('n', function() { 
  carouselSlideToNext();
  if(gMouseTrapDisabled) {return false;}
  gMouseTrapDisabled = true;
  var unfocusedItemIdx = gCurrentlyFocusedItem;
  if (unfocusedItemIdx >= gNumReferences - 1)
  {
    // special case: we're at the end of the list, and we have to set
    // gCurrentlyFocusedItem in such a way that looking at the
    // "previous" item will start by expanding the last one.
    gCurrentlyFocusedItem = gNumReferences;
    gMouseTrapDisabled = false;
    $('#wom-sieve-reload-message').modal('show')
  }
});

// open the currently expanded items' linked page in the browser
Mousetrap.bind('v', function() { 
  var itemToShow = 'wom-ref'+gCurrentlyFocusedItem.toString()+"-url";
  window.open(document.getElementById(itemToShow).href);
});

// Reload the sieve but also makes sure to sync the read state of news
// items on the server before quitting page.
function reloadSieve() 
{
  $('#wom-sieve-reload-message').modal('hide');
  var window_location = window.location;
  if (gReadURLs.length>0) {
    showWarning("wom-sieve-news-loading");
    updateReadStatusOnServer(gReadURLs,function (data) {gReadURLs = []; window_location.reload();});
  }
  else {
    window_location.reload();
  }
}

Mousetrap.bind('r', reloadSieve);


// save the ref corresponding to the currently expanded items
function saveCurrentItem() {
  markAsSaved(gCurrentlyFocusedItem);
}
Mousetrap.bind('b', saveCurrentItem);


Mousetrap.bind('h', switchTitleListDisplay);
