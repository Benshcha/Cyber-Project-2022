using System;
using System.Data;
using System.Configuration;
using System.Linq;
using System.Web;
using System.Web.Security;
using System.Web.UI;
using System.Web.UI.HtmlControls;
using System.Web.UI.WebControls;
using System.Web.UI.WebControls.WebParts;
using System.Xml.Linq;
using System.Data.OleDb;
using System.Web.Caching;

/// <summary>
/// Summary description for MyAdoHelper
/// פעולות עזר לשימוש במסד נתונים מסוג אקסס
///  App_Data המסד ממוקם בתקיה 
///  עודכן וצומצם ע"י יורם 
/// </summary>

public class MyAdoHelper
{
    public static OleDbConnection ConnectToDb(string fileName)
    {
        string path = HttpContext.Current.Server.MapPath("App_Data/");//מיקום מסד בפורוייקט
        path += fileName;
        //לאקסס מ 2010 
        string connString = "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=" + path;//נתוני ההתחברות הכוללים מיקום וסוג המסד
        //לאקסס בגרסה ישנה
        //string connString = "Provider=Microsoft.Jet.OLEDB.4.0;Data source=" + path;//נתוני ההתחברות הכוללים מיקום וסוג המסד
        OleDbConnection conn = new OleDbConnection(connString);
        return conn;
    }

    /// <summary>
    /// To Execute update / insert / delete queries
    ///  הפעולה מקבלת שם קובץ ומשפט לביצוע ומבצעת את הפעולה על המסד
    /// </summary>

    public static int  DoQuery(string fileName, string sql)//הפעולה מקבלת שם מסד נתונים ומחרוזת מחיקה/ הוספה/ עדכון
    //ומבצעת את הפקודה על המסד הפיזי
    {
        OleDbConnection conn = ConnectToDb(fileName);
        conn.Open();
        OleDbCommand com = new OleDbCommand(sql, conn);
        int rowA = com.ExecuteNonQuery();
        com.Dispose();
        conn.Close();
        return rowA;
    }

    /// <summary>
    /// בפעולה מקבלת מסד נתונים ומחרוזת פקודת אס.קיו.אל ומחזירה אובייקט המכיל את כל השורות שעונות לפקודת האס.קיו.אל
    /// </summary>
    public static DataTable ExecuteDataTable(string fileName, string sql)
    {
        OleDbConnection conn = ConnectToDb(fileName);
        conn.Open();
        DataTable dt = new DataTable();
        OleDbDataAdapter tableAdapter = new OleDbDataAdapter(sql,conn);
        tableAdapter.Fill(dt);
        conn.Close();
        return dt;
    }
    // עדכון של טבלה שלימה לבסיס הנתונים, עדכון כולל עדכוני תוכן ומחיקה של שורות בטבלה, 
    //הפעולה מקבלת את שם קובץ מסד הנתונים, פקודה לבחירת כל הרשומות בקובץ , ואובייקט נתונים לעידכון 
    public static void UpdateDataTable(string fileName, string sql, DataTable dt)
    {
        OleDbConnection conn = ConnectToDb(fileName);
        OleDbDataAdapter tableAdapter = new OleDbDataAdapter(sql, conn);
        OleDbCommandBuilder builder = new OleDbCommandBuilder(tableAdapter);
        conn.Open();
        tableAdapter.Update(dt);
        conn.Close();
    }
}
