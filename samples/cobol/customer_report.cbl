       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTOMER-REPORT.
       AUTHOR. LEGACY-SYSTEMS-TEAM.
      *****************************************************************
      * CUSTOMER SALES REPORT GENERATOR                              *
      * GENERATES MONTHLY SALES REPORT FOR CUSTOMER ACCOUNTS         *
      * CALCULATES TOTALS, AVERAGES, AND COMMISSION                  *
      *****************************************************************
       
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE ASSIGN TO "CUSTDATA.DAT"
               ORGANIZATION IS LINE SEQUENTIAL
               FILE STATUS IS WS-FILE-STATUS.
           
           SELECT REPORT-FILE ASSIGN TO "SALESRPT.TXT"
               ORGANIZATION IS LINE SEQUENTIAL.
       
       DATA DIVISION.
       FILE SECTION.
       FD  CUSTOMER-FILE.
       01  CUSTOMER-RECORD.
           05  CUST-ID             PIC 9(6).
           05  CUST-NAME           PIC X(30).
           05  CUST-REGION         PIC X(10).
           05  SALES-AMOUNT        PIC 9(7)V99.
           05  PAYMENT-STATUS      PIC X.
               88  PAID            VALUE 'P'.
               88  PENDING         VALUE 'N'.
       
       FD  REPORT-FILE.
       01  REPORT-LINE             PIC X(80).
       
       WORKING-STORAGE SECTION.
       01  WS-FILE-STATUS          PIC XX.
           88  WS-FILE-OK          VALUE '00'.
           88  WS-FILE-EOF         VALUE '10'.
       
       01  WS-COUNTERS.
           05  WS-TOTAL-CUSTOMERS  PIC 9(5) VALUE ZEROS.
           05  WS-PAID-COUNT       PIC 9(5) VALUE ZEROS.
           05  WS-PENDING-COUNT    PIC 9(5) VALUE ZEROS.
       
       01  WS-TOTALS.
           05  WS-TOTAL-SALES      PIC 9(9)V99 VALUE ZEROS.
           05  WS-PAID-SALES       PIC 9(9)V99 VALUE ZEROS.
           05  WS-PENDING-SALES    PIC 9(9)V99 VALUE ZEROS.
           05  WS-COMMISSION       PIC 9(7)V99 VALUE ZEROS.
       
       01  WS-AVERAGES.
           05  WS-AVG-SALE         PIC 9(7)V99 VALUE ZEROS.
       
       01  WS-CONSTANTS.
           05  WS-COMMISSION-RATE  PIC V999 VALUE 0.075.
           05  WS-HIGH-VALUE-LIMIT PIC 9(7)V99 VALUE 50000.00.
       
       01  WS-REGION-TOTALS.
           05  WS-NORTH-TOTAL      PIC 9(9)V99 VALUE ZEROS.
           05  WS-SOUTH-TOTAL      PIC 9(9)V99 VALUE ZEROS.
           05  WS-EAST-TOTAL       PIC 9(9)V99 VALUE ZEROS.
           05  WS-WEST-TOTAL       PIC 9(9)V99 VALUE ZEROS.
       
       01  WS-REPORT-HEADER.
           05  FILLER              PIC X(25) VALUE SPACES.
           05  FILLER              PIC X(30) 
               VALUE 'MONTHLY CUSTOMER SALES REPORT'.
       
       01  WS-DETAIL-LINE.
           05  DL-CUST-ID          PIC 9(6).
           05  FILLER              PIC X(2) VALUE SPACES.
           05  DL-CUST-NAME        PIC X(30).
           05  FILLER              PIC X(2) VALUE SPACES.
           05  DL-REGION           PIC X(10).
           05  FILLER              PIC X(2) VALUE SPACES.
           05  DL-SALES            PIC $$$,$$$,$$9.99.
           05  FILLER              PIC X(2) VALUE SPACES.
           05  DL-STATUS           PIC X(7).
       
       01  WS-SUMMARY-LINE.
           05  SL-LABEL            PIC X(30).
           05  FILLER              PIC X(2) VALUE SPACES.
           05  SL-VALUE            PIC $$$,$$$,$$9.99.
       
       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
           PERFORM INITIALIZATION
           PERFORM PROCESS-CUSTOMERS
           PERFORM GENERATE-SUMMARY
           PERFORM CLEANUP
           STOP RUN.
       
       INITIALIZATION.
           DISPLAY 'CUSTOMER REPORT GENERATOR - STARTING'
           OPEN INPUT CUSTOMER-FILE
           OPEN OUTPUT REPORT-FILE
           
           IF NOT WS-FILE-OK
               DISPLAY 'ERROR OPENING FILES: ' WS-FILE-STATUS
               STOP RUN
           END-IF
           
           PERFORM WRITE-REPORT-HEADER.
       
       WRITE-REPORT-HEADER.
           WRITE REPORT-LINE FROM WS-REPORT-HEADER
           MOVE SPACES TO REPORT-LINE
           WRITE REPORT-LINE
           MOVE 'ID     NAME                           REGION     '
               TO REPORT-LINE
           STRING 'SALES         STATUS' DELIMITED BY SIZE
               INTO REPORT-LINE WITH POINTER 50
           END-STRING
           WRITE REPORT-LINE
           MOVE ALL '-' TO REPORT-LINE
           WRITE REPORT-LINE.
       
       PROCESS-CUSTOMERS.
           PERFORM READ-CUSTOMER
           PERFORM UNTIL WS-FILE-EOF
               PERFORM PROCESS-CUSTOMER-RECORD
               PERFORM READ-CUSTOMER
           END-PERFORM.
       
       READ-CUSTOMER.
           READ CUSTOMER-FILE
               AT END SET WS-FILE-EOF TO TRUE
           END-READ.
       
       PROCESS-CUSTOMER-RECORD.
           ADD 1 TO WS-TOTAL-CUSTOMERS
           ADD SALES-AMOUNT TO WS-TOTAL-SALES
           
           EVALUATE TRUE
               WHEN PAID
                   ADD 1 TO WS-PAID-COUNT
                   ADD SALES-AMOUNT TO WS-PAID-SALES
               WHEN PENDING
                   ADD 1 TO WS-PENDING-COUNT
                   ADD SALES-AMOUNT TO WS-PENDING-SALES
           END-EVALUATE
           
           PERFORM ACCUMULATE-REGION-TOTALS
           PERFORM CALCULATE-COMMISSION
           PERFORM WRITE-DETAIL-LINE.
       
       ACCUMULATE-REGION-TOTALS.
           EVALUATE CUST-REGION
               WHEN 'NORTH'
                   ADD SALES-AMOUNT TO WS-NORTH-TOTAL
               WHEN 'SOUTH'
                   ADD SALES-AMOUNT TO WS-SOUTH-TOTAL
               WHEN 'EAST'
                   ADD SALES-AMOUNT TO WS-EAST-TOTAL
               WHEN 'WEST'
                   ADD SALES-AMOUNT TO WS-WEST-TOTAL
           END-EVALUATE.
       
       CALCULATE-COMMISSION.
           IF SALES-AMOUNT > WS-HIGH-VALUE-LIMIT
               COMPUTE WS-COMMISSION = WS-COMMISSION + 
                   (SALES-AMOUNT * WS-COMMISSION-RATE * 1.5)
           ELSE
               COMPUTE WS-COMMISSION = WS-COMMISSION + 
                   (SALES-AMOUNT * WS-COMMISSION-RATE)
           END-IF.
       
       WRITE-DETAIL-LINE.
           MOVE CUST-ID TO DL-CUST-ID
           MOVE CUST-NAME TO DL-CUST-NAME
           MOVE CUST-REGION TO DL-REGION
           MOVE SALES-AMOUNT TO DL-SALES
           
           IF PAID
               MOVE 'PAID' TO DL-STATUS
           ELSE
               MOVE 'PENDING' TO DL-STATUS
           END-IF
           
           WRITE REPORT-LINE FROM WS-DETAIL-LINE.
       
       GENERATE-SUMMARY.
           MOVE SPACES TO REPORT-LINE
           WRITE REPORT-LINE
           MOVE ALL '=' TO REPORT-LINE
           WRITE REPORT-LINE
           MOVE SPACES TO REPORT-LINE
           WRITE REPORT-LINE
           
           MOVE 'TOTAL CUSTOMERS:' TO SL-LABEL
           MOVE WS-TOTAL-CUSTOMERS TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           
           MOVE 'TOTAL SALES:' TO SL-LABEL
           MOVE WS-TOTAL-SALES TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           
           IF WS-TOTAL-CUSTOMERS > 0
               COMPUTE WS-AVG-SALE = WS-TOTAL-SALES / 
                   WS-TOTAL-CUSTOMERS
               MOVE 'AVERAGE SALE:' TO SL-LABEL
               MOVE WS-AVG-SALE TO SL-VALUE
               WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           END-IF
           
           MOVE 'TOTAL COMMISSION:' TO SL-LABEL
           MOVE WS-COMMISSION TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           
           PERFORM WRITE-REGION-SUMMARY
           PERFORM WRITE-STATUS-SUMMARY.
       
       WRITE-REGION-SUMMARY.
           MOVE SPACES TO REPORT-LINE
           WRITE REPORT-LINE
           MOVE 'REGIONAL BREAKDOWN:' TO REPORT-LINE
           WRITE REPORT-LINE
           
           MOVE 'NORTH REGION:' TO SL-LABEL
           MOVE WS-NORTH-TOTAL TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           
           MOVE 'SOUTH REGION:' TO SL-LABEL
           MOVE WS-SOUTH-TOTAL TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           
           MOVE 'EAST REGION:' TO SL-LABEL
           MOVE WS-EAST-TOTAL TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           
           MOVE 'WEST REGION:' TO SL-LABEL
           MOVE WS-WEST-TOTAL TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE.
       
       WRITE-STATUS-SUMMARY.
           MOVE SPACES TO REPORT-LINE
           WRITE REPORT-LINE
           MOVE 'PAYMENT STATUS SUMMARY:' TO REPORT-LINE
           WRITE REPORT-LINE
           
           MOVE 'PAID ACCOUNTS:' TO SL-LABEL
           MOVE WS-PAID-COUNT TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           
           MOVE 'PAID SALES TOTAL:' TO SL-LABEL
           MOVE WS-PAID-SALES TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           
           MOVE 'PENDING ACCOUNTS:' TO SL-LABEL
           MOVE WS-PENDING-COUNT TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE
           
           MOVE 'PENDING SALES TOTAL:' TO SL-LABEL
           MOVE WS-PENDING-SALES TO SL-VALUE
           WRITE REPORT-LINE FROM WS-SUMMARY-LINE.
       
       CLEANUP.
           CLOSE CUSTOMER-FILE
           CLOSE REPORT-FILE
           DISPLAY 'REPORT GENERATION COMPLETE'
           DISPLAY 'TOTAL CUSTOMERS PROCESSED: ' WS-TOTAL-CUSTOMERS
           DISPLAY 'TOTAL SALES: $' WS-TOTAL-SALES
           DISPLAY 'REPORT SAVED TO: SALESRPT.TXT'.

      *> Made with Bob
