from xml.etree import ElementTree

class Feed:

  def __init__(self):
    self.title= "unknown"
    self.xmlUrl = "<none>"
    self.htmlUrl = "<none>"
    self.tags = set()
    
  def __str__(self):
    return "Feed: %s\n- %s\n- %s\n- %s" % (self.title.encode("utf-8"),self.xmlUrl,self.htmlUrl,",".join(self.tags))
  
def warning(txt):
  print "WARNING: " + txt
  
# OPML spec:
# http://dev.opml.org/spec2.html

def parse_opml(opml_file,isPath=True):
  if isPath:
    tree = ElementTree.parse(opml_file)
    root = tree.getroot()
  else:
    root = ElementTree.fromstring(opml_file)
  if root.tag != "opml":
    raise RuntimeError("Not an opml file (expected <opml >root tag but found <%s>)" % root.tag)
  opml_version = root.attrib.get("version",None)
  if opml_version is None or opml_version[0] not in ("1","2"):
    raise RuntimeError("Unhandled opml version: %s"% opml_version)
  opml_body = root.find("body")
  current_tags = set()
  collected_feeds = set()
  collected_tags = set()
  parse_outlines(opml_body,current_tags,collected_feeds,collected_tags)
  return collected_feeds,collected_tags

  
def parse_outlines(parent_tag,current_tags,collected_feeds,collected_tags):
  for outline in parent_tag:
    if outline.tag != "outline":
      warning("Ignoring tag that is not an <outline> but a <%s>" % outline.tag)
      continue
    outline_text = outline.attrib.get("text",None)
    if outline_text is None:
      warning("Ignoring attributes of an outline tag who has no text: %s" % outline_text)
      new_current_tags = current_tags.copy()
      parse_outlines(outline,new_current_tags,collected_feeds,collected_tags)
    elif "xmlUrl" not in outline.attrib:
      if outline.attrib.get("type",None) in ("rss","atom"):
        warning("Ignoring attributes of an outline tag who has no xmlUrl attribute but looks like a feed anyway: %s" % outline.attrib)
      else:
        # here we use the outline text as a tag
        new_current_tags = current_tags.copy()
        text_as_tag = outline.attrib.get("text")
        if text_as_tag:
          new_current_tags.add(text_as_tag)
        parse_outlines(outline,new_current_tags,collected_feeds,collected_tags)
    else:
      # this is most probably a feed's link, so let's process it as one
      current_xmlUrl = outline.attrib["xmlUrl"]
      current_feed = None
      for previousFeed in collected_feeds:
        if previousFeed.xmlUrl == current_xmlUrl:
          current_feed = previousFeed
          break
      if current_feed is None:
        current_feed = Feed()
        current_feed.xmlUrl = current_xmlUrl
        # TODO check the conformity of these attributes in the case
        # when a previousFeed with the same xmlUrl has been found
        current_feed.title = outline.attrib["text"]
        current_feed.htmlUrl = outline.attrib.get("htmlUrl",None)
      category_as_txt = outline.attrib.get("category","")
      if category_as_txt:
        category = category_as_txt.split(",")
      else:
        category = []
      current_feed.tags |= current_tags.union(category)
      # update the list of tags
      collected_tags.update(current_feed.tags)
      collected_feeds.add(current_feed)



if __name__ == '__main__':
  collected_feeds,collected_tags = parse_opml("./google-reader-subscriptions.xml")
  print "Feeds:\n\t" + "\n\t".join(str(f) for f in collected_feeds)
  print "Tags:\n\t" + "\n\t".join(collected_tags)
  
