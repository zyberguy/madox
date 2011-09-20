#!/usr/bin/env python

import Image
import lxml.etree as ET
import sys

class SVGCreator:
  def __init__(self, height, width):
    self.root = ET.Element("svg")
    self.root.set("xmlns","http://www.w3.org/2000/svg")
    self.root.set("width", width)
    self.root.set("height", height)
    self.root.set("version", "1.1")

  def add_circle(self, x, y, r, stroke, stroke_width, fill):
    et_circle = ET.SubElement(self.root, "circle")
    et_circle.set("cx", x)
    et_circle.set("cy", y)
    et_circle.set("r", r)
    et_circle.set("stroke", stroke)
    et_circle.set("stroke-width", stroke_width)
    et_circle.set("fill", fill)

  def add_rect(self, x, y, h, w, stroke, stroke_width, fill):
    et_circle = ET.SubElement(self.root, "rect")
    et_circle.set("x", x)
    et_circle.set("y", y)
    et_circle.set("height", h)
    et_circle.set("width", w)
    et_circle.set("stroke", stroke)
    et_circle.set("stroke-width", stroke_width)
    et_circle.set("fill", fill)
      
  def write_to_file(self, outfilename):
    tree = ET.ElementTree(self.root)
    tree.write(outfilename, pretty_print=True)

if __name__ == "__main__":
  """
  Image to SVG cutout converter, done for Ponoko cutting in mind :)
  www.madox.net
  """

  pixel_size = 6 #mm
  max_cut_size = 5.0 #mm
  min_cut_size = 0.5 #mm
  #These are good for a 64x64 image on Ponokos P2 size
  
  try:
    infilename = sys.argv[1:][0]
  except:
    sys.exit("Usage: Python im2svg inputimage...")
  
  #Open the image
  im = Image.open(infilename)
  width, height = im.size
    
  svgcreator1 = SVGCreator( "%imm" % (height * pixel_size),
                            "%imm" % (width * pixel_size))
  svgcreator2 = SVGCreator( "%imm" % (height * pixel_size),
                            "%imm" % (width * pixel_size))
  
  #Pre-process into single channel data
  im = im.convert("L")  #Convert the image to grey scale
  #im = im.convert("1")  #Convert the image to black and white
  
  #Write the pixels
  for y in range(height):
    for x in range(width):
      z = (255-float(im.getpixel((x,y))))/255
      #Original code biased everything to darker, new code simply loses/
      #truncates 'depth' when the pixel is really bright
      #i.e. if it is very bright, just make it the brightest to save on
      #laser cutting some really tiny holes (and to make more solid).
      #cut_radius = (z*(max_cut_size-min_cut_size) + min_cut_size)/2.0
      cut_radius = z*(max_cut_size)/2.0
      if cut_radius > min_cut_size:
        #Note the shapes are created with black infills for visualisation
        svgcreator1.add_circle( "%imm" % (pixel_size*(x+0.5)),
                                "%imm" % (pixel_size*(y+0.5)),
                                "%fmm" % cut_radius,
                                "blue",
                                "0.01mm",
                                "black")
        svgcreator2.add_rect( "%fmm" % (pixel_size*(x+0.5)-cut_radius),
                              "%fmm" % (pixel_size*(y+0.5)-cut_radius),
                              "%fmm" % (cut_radius*2),
                              "%fmm" % (cut_radius*2),
                              "blue",
                              "0.01mm",
                              "black")
        #Black fill needs to be removed before sending to say Ponoko.
        #Makes it much easier to visualise to check result ;)
  
  svgcreator1.write_to_file("circle.svg") #Prettier?
  svgcreator2.write_to_file("square.svg") #Cheaper to cut at Ponoko
