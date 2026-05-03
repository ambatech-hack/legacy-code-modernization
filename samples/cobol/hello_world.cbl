       IDENTIFICATION DIVISION.
       PROGRAM-ID. HELLOWORLD.
       AUTHOR. LEGACY SYSTEM.
       DATE-WRITTEN. 1985-01-01.
       
       ENVIRONMENT DIVISION.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-MESSAGE PIC X(50) VALUE 'Hello, World!'.
       01 WS-COUNTER PIC 9(3) VALUE 0.
       
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           DISPLAY WS-MESSAGE.
           PERFORM DISPLAY-COUNTER.
           STOP RUN.
           
       DISPLAY-COUNTER.
           ADD 1 TO WS-COUNTER.
           DISPLAY 'Counter: ' WS-COUNTER.

      *> Made with Bob
