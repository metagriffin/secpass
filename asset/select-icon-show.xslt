<stylesheet
 version="1.0"
 xmlns="http://www.w3.org/1999/XSL/Transform"
 xmlns:svg="http://www.w3.org/2000/svg"
 xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
 >
 <output method="xml"/>
 <template match="svg:g[@inkscape:groupmode='layer']">
  <copy>
   <apply-templates select="@*"/>
   <choose>
    <when test="@inkscape:label='shadow' or @inkscape:label='show'">
     <attribute name="style">display:inline</attribute>
    </when>
    <otherwise>
     <attribute name="style">display:none</attribute>
    </otherwise>
   </choose>
   <apply-templates select="node()"/>
  </copy>
 </template>
 <template match="@*|node()">
  <copy>
   <apply-templates select="@*|node()"/>
  </copy>
 </template>
</stylesheet>
