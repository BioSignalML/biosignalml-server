######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: xsl.py,v 2225129d2f7b 2011/02/04 01:05:15 dave $
#
######################################################


PAGEXSL = """<?xml version='1.0'?>
         <!DOCTYPE xsl:stylesheet [
           <!ENTITY nbsp "<xsl:text
             xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
             disable-output-escaping='yes'>&#160;</xsl:text>">
           ]
         >
         <xsl:stylesheet
          xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
          version='1.0'>

          <xsl:param name="yscale"          select="2.1"/>  <!-- 2.0em per row -->
          <xsl:param name="form-yscale"     select="1.5"/>
          <xsl:param name="extra-form-line" select="1"/>
          <xsl:param name="col-offset"      select="1"/>    <!-- Subtract from 'col' -->

          <xsl:param name="header-logo"  select="''"/>
          <xsl:param name="header-title" select="''"/>

          <xsl:output method="html"
           doctype-public='"-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"'
           encoding="iso-8859-1"
           indent="no"/>

          <xsl:template match="script">
          <!--=====================-->
           <script type="text/javascript">
            <xsl:choose>
             <xsl:when test="@src">
              <xsl:attribute name="src"><xsl:value-of select="@src"/></xsl:attribute>
             </xsl:when>
             <xsl:otherwise>
              <xsl:value-of select="text()"/>
             </xsl:otherwise>
            </xsl:choose>
           </script>
          </xsl:template>

          <xsl:template match="item">
          <!--====================-->
           <li>
            <a href="/{@action}" title="{@prompt}" onClick="return oktoexit(this)"><xsl:value-of select="@prompt"/></a>
           </li>
          </xsl:template>

          <xsl:template match="menu/menu">
          <!--=========================-->
           <xsl:choose>
            <xsl:when test="@action">
             <li>
              <a href="/{@action}" title="{@prompt}"
                onClick="return oktoexit(this)"><xsl:value-of select="@prompt"/></a>
              <xsl:if test="count(item)"><ul class="sub_menu"><xsl:apply-templates /></ul></xsl:if>
             </li>
            </xsl:when>
            <xsl:when test="@prompt">
             <li>
              <span class="menu"><xsl:value-of select="@prompt"/></span>
              <xsl:if test="count(item)"><ul class="sub_menu"><xsl:apply-templates /></ul></xsl:if>
             </li>
            </xsl:when>
           </xsl:choose>
          </xsl:template>

          <xsl:template match="menu">
          <!--====================-->
           <ul class="jd_menu"><xsl:apply-templates /></ul>
          </xsl:template>

          <xsl:template match="tree">
          <!--====================-->
           <xsl:variable name="theme">
            <xsl:choose>
             <xsl:when test="@theme"><xsl:value-of select="@theme"/></xsl:when>
             <xsl:otherwise>default</xsl:otherwise>
            </xsl:choose>
           </xsl:variable>
           <script type="text/javascript">
            $(function () {
              $.jstree._themes = "/static/themes/" ;
              $("#tree").jstree({
                core: { animation: 0 },
			             plugins: [ "themes", "html_data" ],
                themes: { theme: "<xsl:value-of select="$theme"/>", dots: true, icons: true }
                }) ;
              }) ;
           </script>
           <div class="jstree" id="tree">
            <ul><xsl:apply-templates /></ul>
           </div>
          </xsl:template>

          <xsl:template match="subtree">
          <!--====================-->
           <ul><xsl:apply-templates /></ul>
          </xsl:template>

          <xsl:template name="tree-action">
          <!--==========================-->
           <xsl:choose>
            <xsl:when test="@action">
             <a href="{@action}" class="cluetip" id="{@id}"><xsl:value-of select="text()"/></a>
            </xsl:when>
            <xsl:otherwise>
             <span><xsl:value-of select="text()"/></span>
            </xsl:otherwise>
           </xsl:choose>
          </xsl:template>

          <xsl:template match="node">
          <!--====================-->
           <li class="{@class}">
            <xsl:call-template name="tree-action"/>
            <xsl:apply-templates select="subtree | leaf" />
           </li>
          </xsl:template>

          <xsl:template match="leaf">
          <!--====================-->
           <li class="{@class}">
            <xsl:call-template name="tree-action"/>
           </li>
          </xsl:template>

          <xsl:template match="text">
          <!--====================-->
           <span class="fixed">
            <xsl:if test="@row">
              <xsl:attribute name="style">top:<xsl:value-of
               select="$yscale*(@row - 1)"/>em;<xsl:if test="@col">left:<xsl:value-of
               select="@col - $col-offset"/>em;</xsl:if>
              </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates />
           </span>
          </xsl:template>

          <xsl:template name="prompt">
          <!--=====================-->
           <xsl:if test="@row or @prompt and @prompt != ''">
            <span>
             <xsl:choose>
              <xsl:when test="@row">
               <xsl:attribute name="class">fixed prompt</xsl:attribute>
               <xsl:attribute name="style">top:<xsl:value-of
                select="$yscale*(@row - 1)"/>em;<xsl:if test="@pcol">left:<xsl:value-of
                select="@pcol - $col-offset"/>em;</xsl:if>
               </xsl:attribute>
              </xsl:when>
              <xsl:otherwise>
               <xsl:attribute name="class">prompt</xsl:attribute>
              </xsl:otherwise>
             </xsl:choose>
             <xsl:if test="@prompt and @prompt != ''">
              <xsl:value-of select="@prompt"/><xsl:if test="substring(@prompt, string-length(@prompt)) != '?'">:</xsl:if>
             </xsl:if>
            </span>
           </xsl:if>
          </xsl:template>

          <xsl:template name="help">
          <!--===================-->
           <xsl:if test="@help">
             <span class="fixed">
              <xsl:if test="@row">
                <xsl:attribute name="style">top:<xsl:value-of
                 select="$yscale*(@row - 1)"/>em;<xsl:if test="@hcol">left:<xsl:value-of
                 select="@hcol - $col-offset"/>em;</xsl:if>
                </xsl:attribute>
              </xsl:if>
              <xsl:value-of select="@help"/>
             </span>
           </xsl:if>
          </xsl:template>

          <xsl:template name="input">
          <!--=====================-->
           <xsl:variable name="type">
            <xsl:choose>
             <xsl:when test="@type"><xsl:value-of select="@type"/></xsl:when>
             <xsl:otherwise>text</xsl:otherwise>
            </xsl:choose>
           </xsl:variable>
           <xsl:variable name="width">
            <xsl:choose>
             <xsl:when test="parent::*[@class='search']">
              <xsl:choose>
               <xsl:when test="@size &gt;= 20">18</xsl:when>
               <xsl:otherwise><xsl:value-of select="@size - 2"/></xsl:otherwise>
              </xsl:choose>
             </xsl:when>
             <xsl:otherwise><xsl:value-of select="@size"/></xsl:otherwise>
            </xsl:choose>
           </xsl:variable>
           <xsl:variable name="control-id">
             <xsl:value-of select="@control"/>_<xsl:value-of select="@name"/>
           </xsl:variable>
           <xsl:if test="@control">
            <script type="text/javascript">
             $(function() {
               $("#<xsl:value-of select="$control-id"/>").<xsl:value-of select="@control"/>(<xsl:if test="@params">{ <xsl:value-of select="@params"/> }</xsl:if>);
               });
            </script>
           </xsl:if>
           <input type="{$type}" id="{@name}" name="{@name}" style="width: {0.7*$width}em" maxlength="{@size}" value="{@value}" onChange="changed(this)">
            <xsl:if test="@update='no'"><xsl:attribute name="readonly">yes</xsl:attribute></xsl:if>

            <xsl:if test="not (@update='no')">
             <xsl:choose>
              <xsl:when test="@control"><xsl:attribute name="id"><xsl:value-of select="$control-id"/></xsl:attribute></xsl:when>
              <xsl:otherwise><xsl:attribute name="onFocus">this.select()</xsl:attribute></xsl:otherwise>
             </xsl:choose>
            </xsl:if>
            <xsl:if test="@valid">
             <xsl:choose>
              <xsl:when test="contains(@valid, ' ')">
               <xsl:attribute name="onKeyPress">return valid<xsl:value-of
                select="substring-before(@valid, ' ')"/>(this,event,'<xsl:value-of
                select="substring-after(@valid, ' ')"/>')</xsl:attribute>
              </xsl:when>
              <xsl:otherwise>
               <xsl:attribute name="onKeyPress">return valid<xsl:value-of select="@valid"/>(this,event)</xsl:attribute>
              </xsl:otherwise>
             </xsl:choose>
            </xsl:if>
           </input>
          </xsl:template>

          <xsl:template match="field">
          <!--=====================-->
           <xsl:call-template name="prompt"/>
           <xsl:if test="@type = 'hidden' or @size &gt; 0">
             <xsl:choose>
              <xsl:when test="@row">
               <span>
                <xsl:attribute name="class">fixed</xsl:attribute>
                <xsl:attribute name="style">top:<xsl:value-of
                 select="-0.1+$yscale*(@row - 1)"/>em;<xsl:if test="@fcol">left:<xsl:value-of
                 select="@fcol - $col-offset"/>em;</xsl:if>
                </xsl:attribute>
                <xsl:call-template name="input"/>
               </span>
              </xsl:when>
              <xsl:otherwise>
               <xsl:call-template name="input"/>
              </xsl:otherwise>
             </xsl:choose>
             <xsl:call-template name="help"/>
           </xsl:if>
          </xsl:template>

          <xsl:template match="field[@type='text']">
          <!--===================================-->
           <xsl:call-template name="prompt"/>
           <span class="fixed">
            <xsl:if test="@row">
             <xsl:attribute name="style">top:<xsl:value-of
              select="$yscale*(@row - 1)"/>em;<xsl:if test="@fcol">left:<xsl:value-of
              select="@fcol - $col-offset"/>em;</xsl:if>
             </xsl:attribute>
            </xsl:if>
            <textarea id="{@name}" name="{@name}"
              cols="{@cols}" rows="{@rows}"
              onChange="changed(this)">
             <xsl:if test="@update='no'"><xsl:attribute name="readonly">yes</xsl:attribute></xsl:if>
             <xsl:apply-templates/>
            </textarea>
           </span>
          </xsl:template>

          <xsl:template match="option">
          <!--======================-->
           <option>
            <xsl:if test="@value">
             <xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
            </xsl:if>
            <xsl:if test="@selected">
             <xsl:attribute name="selected"><xsl:value-of select="@selected"/></xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
           </option>
          </xsl:template>

          <xsl:template name="select">
          <!--======================-->
           <select id="{@name}" name="{@name}">
            <xsl:if test="@onchange">
             <xsl:attribute name="onchange"><xsl:value-of select="@onchange"/></xsl:attribute>
            </xsl:if>
            <xsl:if test="@size">
             <xsl:attribute name="style">width: <xsl:value-of select="@size"/>em</xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
           </select>
          </xsl:template>

          <xsl:template match="select">
          <!--======================-->
           <xsl:call-template name="prompt"/>
           <xsl:choose>
            <xsl:when test="@row">
             <span>
              <xsl:attribute name="class">fixed</xsl:attribute>
              <xsl:attribute name="style">top:<xsl:value-of
               select="$yscale*(@row - 1)"/>em;<xsl:if test="@fcol">left:<xsl:value-of
               select="@fcol - $col-offset"/>em;</xsl:if>
              </xsl:attribute>
              <xsl:call-template name="select"/>
             </span>
            </xsl:when>
            <xsl:otherwise>
             <xsl:call-template name="select"/>
            </xsl:otherwise>
           </xsl:choose>
           <xsl:call-template name="help"/>
          </xsl:template>

          <xsl:template match="button">
          <!--======================-->
           <span>
            <xsl:if test="@row">
             <xsl:attribute name="class">fixed</xsl:attribute>
             <xsl:attribute name="style">top:<xsl:value-of
              select="-0.2+$yscale*(@row - 1)"/>em;<xsl:if test="@col">left:<xsl:value-of
              select="@col - $col-offset"/>em;</xsl:if>
             </xsl:attribute>
            </xsl:if>
            <xsl:choose>
             <xsl:when test="@type='reset'">
              <input class="button" type="reset" value="{@prompt}" onClick="resetform(this)"/>
             </xsl:when>
             <xsl:otherwise>
              <input class="button" type="submit" name="{@name}" value="{@prompt}">
               <xsl:if test="@onclick"><xsl:attribute name="onClick">return <xsl:value-of select="@onclick"/></xsl:attribute></xsl:if>
              </input>
             </xsl:otherwise>
            </xsl:choose>
           </span>
          </xsl:template>

          <xsl:template match="form">
          <!--====================-->
           <div>
            <xsl:attribute name="class">
             <xsl:choose>
              <xsl:when test="@class"><xsl:value-of select="@class"/></xsl:when>
              <xsl:otherwise>formbox</xsl:otherwise>    <!-- IE box model hack... -->
             </xsl:choose>
            </xsl:attribute>
            <xsl:if test="@width or @height">
             <xsl:attribute name="style">
              <xsl:if test="@width">width: <xsl:value-of select="@width"/>em;</xsl:if>
              <xsl:if test="@height">height: <xsl:value-of select="$form-yscale*(@height+$extra-form-line)"/>em;</xsl:if>
             </xsl:attribute>
            </xsl:if>
            <div>
             <xsl:attribute name="class">
              <xsl:choose>
               <xsl:when test="@layout"><xsl:value-of select="@layout"/></xsl:when>
               <xsl:otherwise>form</xsl:otherwise>
              </xsl:choose>
             </xsl:attribute>
             <form method="post" action="{@action}" id="form" autocomplete="off">
              <input type="hidden" name="form_key" value="{@key}"/> 
              <input type="hidden" name="form_tab" value="{@tab}"/> 
              <input type="hidden" name="form_op"  value=""/> 
              <xsl:apply-templates select="field | select | text | button | table | script"/>
             </form>
            </div>
           </div>
          </xsl:template>

          <xsl:template match="searchform">
          <!--==========================-->
           <div class="formbox">
            <div class="form">
             <form method="post" action="{@action}" id="searchform" autocomplete="off">
              <div class="search">
               <div class="line">
                <div class="col1">
                 <span class="title"><xsl:value-of select="text()"/></span>
                </div>
                <div class="col2"></div>
                <div class="col3"><button class='del'>-</button></div>
                <div class="clear">&nbsp;</div>
               </div>
              </div>
              <button class='add'>+</button>
              <span class="right">
               <input class="button" type="submit" name="action" value="Search"/>
              </span>
             </form>
            </div>
           </div>
           <div id="searchresults">
           </div>
          </xsl:template>

          <xsl:template match="link">
          <!--====================-->
           <a href="{@href}" onClick="return oktoexit(this)"><xsl:apply-templates /></a>
          </xsl:template>

          <xsl:template match="link[@type='img']">
          <!--=================================-->
           <a href="{@href}"><img alt="{@alt}" title="{@alt}" border="0">
            <xsl:attribute name="src">/static/<xsl:value-of select="@src"/></xsl:attribute> 
           </img></a>
          </xsl:template>

          <xsl:template match="btnlink">
          <!--=======================-->
           <a href="{@href}" class="btn"><xsl:apply-templates /></a>
          </xsl:template>


          <xsl:template match="emphasis">
          <!--========================-->
           <span class="emphasised"><xsl:apply-templates /></span>
          </xsl:template>

          <xsl:template match="block">
          <!--=====================-->
           <div class="block">
            <xsl:apply-templates />
           </div>
          </xsl:template>

          <xsl:template match="td">
          <!--==================-->
           <td>
            <xsl:if test='@colspan'>
             <xsl:attribute name='colspan'><xsl:value-of select='@colspan'/></xsl:attribute>
            </xsl:if><xsl:if test='@class'>
             <xsl:attribute name='class'><xsl:value-of select='@class'/></xsl:attribute>
            </xsl:if><xsl:if test='@align'>
             <xsl:attribute name='align'><xsl:value-of select='@align'/></xsl:attribute>
            </xsl:if><xsl:apply-templates /></td>
          </xsl:template>

          <xsl:template match="th">
          <!--==================-->
           <th>
            <xsl:if test='@colspan'>
             <xsl:attribute name='colspan'><xsl:value-of select='@colspan'/></xsl:attribute>
            </xsl:if><xsl:if test='@class'>
             <xsl:attribute name='class'><xsl:value-of select='@class'/></xsl:attribute>
            </xsl:if><xsl:if test='@align'>
             <xsl:attribute name='align'><xsl:value-of select='@align'/></xsl:attribute>
            </xsl:if><xsl:apply-templates /></th>
          </xsl:template>

          <xsl:template match="tr">
          <!--==================-->
           <tr>
            <xsl:if test='@class'>
             <xsl:attribute name='class'><xsl:value-of select='@class'/></xsl:attribute>
            </xsl:if><xsl:apply-templates /></tr>
          </xsl:template>

          <xsl:template match="form/table">
          <!--==========================-->
           <div class="table">
            <span class="fixed">
             <xsl:if test="@width">
              <xsl:attribute name="style">width: <xsl:value-of
               select="@width"/>em;<xsl:if test="@row">top: <xsl:value-of
               select="-0.2+$yscale*(@row - 1)"/>em;</xsl:if><xsl:if test="@col">left: <xsl:value-of
               select="@col - $col-offset"/>em;</xsl:if>
              </xsl:attribute>
             </xsl:if>
             <xsl:if test="@title"><div class="tabletitle"><xsl:value-of select="@title"/></div></xsl:if>
             <table class="form"><xsl:apply-templates /></table>
            </span>
           </div>
          </xsl:template>

          <xsl:template match="form[@class]/table">
          <!--==================================-->
           <div class="table">
            <xsl:if test="@title"><div class="tabletitle"><xsl:value-of select="@title"/></div></xsl:if>
            <table class="form"><xsl:apply-templates /></table>
           </div>
          </xsl:template>

          <xsl:template match="table">
          <!--====================-->
           <div class="table">
            <xsl:if test="../form/@width">
             <xsl:attribute name="style">width: <xsl:value-of select="../form/@width"/>em;</xsl:attribute>
            </xsl:if>
            <table class="field"><xsl:apply-templates /></table>
           </div>
          </xsl:template>


          <xsl:template match="tab">
          <!--===================-->
            <xsl:choose>
             <xsl:when test="@name=../@selected">
              <span class="sel"><xsl:value-of select="@prompt"/></span>
             </xsl:when>
             <xsl:otherwise>
              <a onClick="return oktoexit(this)">
               <xsl:attribute name="href"><xsl:value-of select="@action"/>&amp;tab=<xsl:value-of select="@name"/></xsl:attribute>
               <xsl:value-of select="@prompt"/>
              </a>
             </xsl:otherwise>
            </xsl:choose>
          </xsl:template>

          <xsl:template match="tabs">
          <!--====================-->
           <div class="tabs"><xsl:apply-templates select="tab"/></div>
          </xsl:template>


          <xsl:template match="@*|node()">    <!-- Copy everything not otherwise matched -->
          <!--=========================-->
           <xsl:copy>  
            <xsl:apply-templates select="@*|node()"/>  
           </xsl:copy>  
          </xsl:template>


          <xsl:template match="page/title">
          <!--==========================-->
           <div class="title">
            <xsl:if test="../form/@width">
             <xsl:attribute name="style">width: <xsl:value-of select="../form/@width"/>em;</xsl:attribute>
            </xsl:if>
            <h1><xsl:apply-templates /></h1>
           </div>
          </xsl:template>


          <xsl:template match="stylesheet">
          <!--==========================-->
           <xsl:choose>
            <xsl:when test="@src">
             <link type="text/css" href="{@src}" rel="stylesheet"/>
            </xsl:when>
            <xsl:otherwise>
             <style>
              <xsl:value-of select="text()"/>
             </style>
            </xsl:otherwise>
           </xsl:choose>
          </xsl:template>


          <xsl:template match="page">
          <!--====================-->
           <html xmlns="http://www.w3.org/1999/xhtml">
            <head>
             <title>BioSignalML Repository</title>
             <xsl:if test="@refresh"><meta http-equiv='Refresh' content='{@refresh}'/></xsl:if>
             <link rel="shortcut icon" href="/static/favicon.ico"/>
             <script type="text/javascript" src="/static/script/validation.js"/>
             <script type="text/javascript" src="/static/script/jquery-1.5.js"/>
<!--             <script type="text/javascript" src="/static/script/jquery-1.5.min.js"/>  -->
             <script type="text/javascript" src="/static/script/jquery-ui-1.8.9.min.js"/>
             <script type="text/javascript" src="/static/script/jquery-ui-datetimepicker.js"/>
            	<script type="text/javascript" src="/static/script/jquery.jstree.js"/>
            	<script type="text/javascript" src="/static/script/jquery.jdMenu.js"/>
            	<script type="text/javascript" src="/static/script/jquery.positionBy.js"/>
             <script type="text/javascript" src="/static/script/jquery.hoverIntent.js"/>
             <script type="text/javascript" src="/static/script/jquery.cluetip.js"/>
             <script type="text/javascript" src="/static/script/json2.js"/>
             <script type="text/javascript" src="/static/script/comet.js"/>
             <script type="text/javascript" src="/static/script/repository.js"/>
             <link type="text/css" href="/static/css/stylesheet.css" rel="stylesheet"/>
             <xsl:apply-templates select="stylesheet"/>
            </head>
            <body>
             <xsl:if test="@alert != ''">
              <xsl:attribute name="onload">alert("<xsl:value-of select="@alert"/>")</xsl:attribute>
             </xsl:if>
             <xsl:if test="@keypress != ''">
              <xsl:attribute name="onkeydown"><xsl:value-of select="@keypress"/>(event)</xsl:attribute>
             </xsl:if>
             <noscript>These pages use Javascript - please enable it in your browser</noscript>
             <div id="header">
              <h1><xsl:value-of select="$header-title"/></h1>
              <div class="spacer"></div>
              <div id="menubar">
               <xsl:apply-templates select="menu"/>
              </div>
             </div>
             <div id="message"><xsl:apply-templates select="message"/></div>
             <div id="content">
              <xsl:apply-templates select="title"/>
              <xsl:apply-templates select="tabs"/>
              <div id="contentbody">
                <xsl:apply-templates select="*[not(name()='menu'
                                                or name()='tabs'
                                                or name()='title'
                                                or name()='message'
                                                or name()='stylesheet'
                                             )]"/>
              </div>
             </div>
             <div id="footer">
             </div>

            </body>
           </html>
          </xsl:template>

         </xsl:stylesheet>"""
