       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYROLL-SYSTEM.
       AUTHOR. LEGACY-TEAM.
       DATE-WRITTEN. 1998-03-15.
       DATE-COMPILED.
      *================================================================*
      * PAYROLL PROCESSING SYSTEM - LEGACY COBOL                       *
      * Calculates employee salary, tax deductions, and net pay         *
      * Supports: Regular, Overtime, and Contract employees             *
      *================================================================*

       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SOURCE-COMPUTER. IBM-MAINFRAME.
       OBJECT-COMPUTER. IBM-MAINFRAME.

       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT EMPLOYEE-FILE ASSIGN TO 'EMPFILE.DAT'
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT PAYROLL-REPORT ASSIGN TO 'PAYROLL.RPT'
               ORGANIZATION IS LINE SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  EMPLOYEE-FILE
           LABEL RECORDS ARE STANDARD.
       01  EMPLOYEE-RECORD.
           05 EMP-ID              PIC 9(6).
           05 EMP-NAME            PIC X(30).
           05 EMP-TYPE            PIC X(1).
              88 REGULAR-EMPLOYEE    VALUE 'R'.
              88 OVERTIME-EMPLOYEE   VALUE 'O'.
              88 CONTRACT-EMPLOYEE   VALUE 'C'.
           05 EMP-HOURS-WORKED    PIC 9(3)V9(2).
           05 EMP-HOURLY-RATE     PIC 9(5)V9(2).
           05 EMP-DEPARTMENT      PIC X(10).
           05 EMP-TAX-CODE        PIC X(2).

       FD  PAYROLL-REPORT
           LABEL RECORDS ARE STANDARD.
       01  REPORT-LINE            PIC X(132).

       WORKING-STORAGE SECTION.
       01  WS-FLAGS.
           05 WS-EOF-FLAG         PIC X(1) VALUE 'N'.
              88 END-OF-FILE         VALUE 'Y'.
           05 WS-ERROR-FLAG       PIC X(1) VALUE 'N'.
              88 HAS-ERROR           VALUE 'Y'.

       01  WS-COUNTERS.
           05 WS-RECORD-COUNT     PIC 9(5)   VALUE ZEROES.
           05 WS-ERROR-COUNT      PIC 9(5)   VALUE ZEROES.
           05 WS-TOTAL-GROSS      PIC 9(9)V99 VALUE ZEROES.
           05 WS-TOTAL-NET        PIC 9(9)V99 VALUE ZEROES.
           05 WS-TOTAL-TAX        PIC 9(9)V99 VALUE ZEROES.

       01  WS-CALCULATIONS.
           05 WS-REGULAR-HOURS    PIC 9(3)V99 VALUE ZEROES.
           05 WS-OVERTIME-HOURS   PIC 9(3)V99 VALUE ZEROES.
           05 WS-OVERTIME-RATE    PIC 9(5)V99 VALUE ZEROES.
           05 WS-GROSS-PAY        PIC 9(7)V99 VALUE ZEROES.
           05 WS-TAX-AMOUNT       PIC 9(7)V99 VALUE ZEROES.
           05 WS-TAX-RATE         PIC 9(3)V99 VALUE ZEROES.
           05 WS-NET-PAY          PIC 9(7)V99 VALUE ZEROES.
           05 WS-BONUS            PIC 9(7)V99 VALUE ZEROES.

       01  WS-CONSTANTS.
           05 WS-OVERTIME-LIMIT   PIC 9(3)    VALUE 40.
           05 WS-OVERTIME-MULT    PIC 9(1)V99 VALUE 1.50.
           05 WS-TAX-LOW-RATE     PIC 9(3)V99 VALUE 15.00.
           05 WS-TAX-MID-RATE     PIC 9(3)V99 VALUE 25.00.
           05 WS-TAX-HIGH-RATE    PIC 9(3)V99 VALUE 35.00.
           05 WS-TAX-LOW-LIMIT    PIC 9(7)V99 VALUE 3000.00.
           05 WS-TAX-MID-LIMIT    PIC 9(7)V99 VALUE 8000.00.

       01  WS-REPORT-HEADERS.
           05 WS-HEADER-1.
              10 FILLER           PIC X(20) VALUE SPACES.
              10 FILLER           PIC X(30)
                 VALUE 'MONTHLY PAYROLL PROCESSING REPORT'.
              10 FILLER           PIC X(82) VALUE SPACES.
           05 WS-HEADER-2.
              10 FILLER           PIC X(132) VALUE ALL '-'.
           05 WS-HEADER-3.
              10 FILLER           PIC X(6)  VALUE 'EMP ID'.
              10 FILLER           PIC X(2)  VALUE SPACES.
              10 FILLER           PIC X(20) VALUE 'NAME'.
              10 FILLER           PIC X(6)  VALUE 'TYPE  '.
              10 FILLER           PIC X(10) VALUE 'DEPT      '.
              10 FILLER           PIC X(12) VALUE 'GROSS PAY   '.
              10 FILLER           PIC X(12) VALUE 'TAX         '.
              10 FILLER           PIC X(12) VALUE 'NET PAY     '.
              10 FILLER           PIC X(52) VALUE SPACES.

       01  WS-DETAIL-LINE.
           05 WD-EMP-ID           PIC 9(6).
           05 FILLER              PIC X(2) VALUE SPACES.
           05 WD-EMP-NAME         PIC X(20).
           05 WD-EMP-TYPE         PIC X(6).
           05 WD-DEPARTMENT       PIC X(10).
           05 WD-GROSS-PAY        PIC ZZZ,ZZZ.99.
           05 FILLER              PIC X(3) VALUE SPACES.
           05 WD-TAX-AMOUNT       PIC ZZZ,ZZZ.99.
           05 FILLER              PIC X(3) VALUE SPACES.
           05 WD-NET-PAY          PIC ZZZ,ZZZ.99.
           05 FILLER              PIC X(46) VALUE SPACES.

       01  WS-SUMMARY-LINE.
           05 FILLER              PIC X(30)
              VALUE 'TOTALS: '.
           05 WS-SUM-GROSS        PIC ZZZ,ZZZ,ZZZ.99.
           05 FILLER              PIC X(3) VALUE SPACES.
           05 WS-SUM-TAX          PIC ZZZ,ZZZ,ZZZ.99.
           05 FILLER              PIC X(3) VALUE SPACES.
           05 WS-SUM-NET          PIC ZZZ,ZZZ,ZZZ.99.
           05 FILLER              PIC X(43) VALUE SPACES.

       PROCEDURE DIVISION.
       0000-MAIN-PROCEDURE.
           PERFORM 1000-INITIALIZE
           PERFORM 2000-PROCESS-EMPLOYEES
               UNTIL END-OF-FILE
           PERFORM 3000-PRINT-SUMMARY
           PERFORM 9000-FINALIZE
           STOP RUN.

       1000-INITIALIZE.
           OPEN INPUT  EMPLOYEE-FILE
           OPEN OUTPUT PAYROLL-REPORT
           PERFORM 1100-PRINT-HEADERS
           PERFORM 1200-READ-EMPLOYEE.

       1100-PRINT-HEADERS.
           WRITE REPORT-LINE FROM WS-HEADER-1
           WRITE REPORT-LINE FROM WS-HEADER-2
           WRITE REPORT-LINE FROM WS-HEADER-3
           WRITE REPORT-LINE FROM WS-HEADER-2.

       1200-READ-EMPLOYEE.
           READ EMPLOYEE-FILE
               AT END MOVE 'Y' TO WS-EOF-FLAG
           END-READ.

       2000-PROCESS-EMPLOYEES.
           ADD 1 TO WS-RECORD-COUNT
           PERFORM 2100-VALIDATE-RECORD
           IF NOT HAS-ERROR
               PERFORM 2200-CALCULATE-GROSS-PAY
               PERFORM 2300-CALCULATE-TAX
               PERFORM 2400-CALCULATE-NET-PAY
               PERFORM 2500-UPDATE-TOTALS
               PERFORM 2600-PRINT-DETAIL
           END-IF
           MOVE 'N' TO WS-ERROR-FLAG
           PERFORM 1200-READ-EMPLOYEE.

       2100-VALIDATE-RECORD.
           IF EMP-HOURLY-RATE <= ZEROES
               MOVE 'Y' TO WS-ERROR-FLAG
               ADD 1 TO WS-ERROR-COUNT
               DISPLAY 'ERROR: Invalid hourly rate for EMP ' EMP-ID
           END-IF
           IF EMP-HOURS-WORKED > 80
               MOVE 'Y' TO WS-ERROR-FLAG
               ADD 1 TO WS-ERROR-COUNT
               DISPLAY 'ERROR: Hours exceeded limit for EMP ' EMP-ID
           END-IF.

       2200-CALCULATE-GROSS-PAY.
           MOVE ZEROES TO WS-GROSS-PAY
           MOVE ZEROES TO WS-BONUS

           IF REGULAR-EMPLOYEE
               IF EMP-HOURS-WORKED > WS-OVERTIME-LIMIT
                   MOVE WS-OVERTIME-LIMIT TO WS-REGULAR-HOURS
                   SUBTRACT WS-OVERTIME-LIMIT FROM EMP-HOURS-WORKED
                       GIVING WS-OVERTIME-HOURS
                   MULTIPLY EMP-HOURLY-RATE BY WS-OVERTIME-MULT
                       GIVING WS-OVERTIME-RATE
                   MULTIPLY WS-OVERTIME-HOURS BY WS-OVERTIME-RATE
                       GIVING WS-GROSS-PAY
                   MULTIPLY WS-REGULAR-HOURS BY EMP-HOURLY-RATE
                       GIVING WS-BONUS
                   ADD WS-BONUS TO WS-GROSS-PAY
               ELSE
                   MULTIPLY EMP-HOURS-WORKED BY EMP-HOURLY-RATE
                       GIVING WS-GROSS-PAY
               END-IF

           ELSE IF OVERTIME-EMPLOYEE
               MULTIPLY EMP-HOURS-WORKED BY EMP-HOURLY-RATE
                   GIVING WS-GROSS-PAY
               MULTIPLY WS-OVERTIME-MULT BY WS-GROSS-PAY
                   GIVING WS-GROSS-PAY

           ELSE IF CONTRACT-EMPLOYEE
               MULTIPLY EMP-HOURS-WORKED BY EMP-HOURLY-RATE
                   GIVING WS-GROSS-PAY
               MULTIPLY 0.90 BY WS-GROSS-PAY
                   GIVING WS-GROSS-PAY
           END-IF.

       2300-CALCULATE-TAX.
           MOVE ZEROES TO WS-TAX-AMOUNT

           IF WS-GROSS-PAY <= WS-TAX-LOW-LIMIT
               MOVE WS-TAX-LOW-RATE TO WS-TAX-RATE
           ELSE IF WS-GROSS-PAY <= WS-TAX-MID-LIMIT
               MOVE WS-TAX-MID-RATE TO WS-TAX-RATE
           ELSE
               MOVE WS-TAX-HIGH-RATE TO WS-TAX-RATE
           END-IF

           MULTIPLY WS-GROSS-PAY BY WS-TAX-RATE
               GIVING WS-TAX-AMOUNT
           DIVIDE 100 INTO WS-TAX-AMOUNT.

       2400-CALCULATE-NET-PAY.
           SUBTRACT WS-TAX-AMOUNT FROM WS-GROSS-PAY
               GIVING WS-NET-PAY.

       2500-UPDATE-TOTALS.
           ADD WS-GROSS-PAY TO WS-TOTAL-GROSS
           ADD WS-TAX-AMOUNT TO WS-TOTAL-TAX
           ADD WS-NET-PAY TO WS-TOTAL-NET.

       2600-PRINT-DETAIL.
           MOVE EMP-ID          TO WD-EMP-ID
           MOVE EMP-NAME        TO WD-EMP-NAME
           MOVE EMP-DEPARTMENT  TO WD-DEPARTMENT
           MOVE WS-GROSS-PAY    TO WD-GROSS-PAY
           MOVE WS-TAX-AMOUNT   TO WD-TAX-AMOUNT
           MOVE WS-NET-PAY      TO WD-NET-PAY

           IF REGULAR-EMPLOYEE
               MOVE 'REG   ' TO WD-EMP-TYPE
           ELSE IF OVERTIME-EMPLOYEE
               MOVE 'OVT   ' TO WD-EMP-TYPE
           ELSE
               MOVE 'CTR   ' TO WD-EMP-TYPE
           END-IF

           WRITE REPORT-LINE FROM WS-DETAIL-LINE.

       3000-PRINT-SUMMARY.
           MOVE WS-TOTAL-GROSS  TO WS-SUM-GROSS
           MOVE WS-TOTAL-TAX    TO WS-SUM-TAX
           MOVE WS-TOTAL-NET    TO WS-SUM-NET
           WRITE REPORT-LINE FROM WS-HEADER-2
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           DISPLAY '========================================='
           DISPLAY 'PAYROLL PROCESSING COMPLETE'
           DISPLAY 'RECORDS PROCESSED : ' WS-RECORD-COUNT
           DISPLAY 'ERRORS FOUND      : ' WS-ERROR-COUNT
           DISPLAY 'TOTAL GROSS PAY   : ' WS-TOTAL-GROSS
           DISPLAY 'TOTAL TAX         : ' WS-TOTAL-TAX
           DISPLAY 'TOTAL NET PAY     : ' WS-TOTAL-NET
           DISPLAY '========================================='.

       9000-FINALIZE.
           CLOSE EMPLOYEE-FILE
           CLOSE PAYROLL-REPORT.
