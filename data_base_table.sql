USE [pythonTesting]
GO

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[barcodes](
	[type] [varchar](450) NULL,
	[data] [varchar](450) NULL,
	[description] [varchar](max) NULL,
	[dateEntered] [datetime] NULL,
 CONSTRAINT [uq_barcodes] UNIQUE NONCLUSTERED 
(
	[type] ASC,
	[data] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[barcodes] ADD  CONSTRAINT [df_barcodes]  DEFAULT (getdate()) FOR [dateEntered]
GO


